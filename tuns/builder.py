from src.cmd  import run_cmd
from src.args import args
import os.path
import sys
import random
import string
import hashlib

key_charset =  string.ascii_letters + string.digits

import tuns.builder

def _clean():
    if os.path.exists("tuns/libtun.a"):
        os.unlink("tuns/libtun.a")

def dns(opt):
    print("[*] Building DNS tunnel...")
    _clean()
    
    obf_str = ""
    if opt["obfuscate"]:
        auth = "".join(random.choices(string.ascii_lowercase, k=len("auth")))
        resource = "".join(random.choices(string.ascii_lowercase, k=len("resource")))
        connect = "".join(random.choices(string.ascii_lowercase, k=len("connect")))
        obf_str = f'-DCUSTOM_STRINGS -DRESOURCE="\\"={resource}.\\"" -DCONNECT="\\"={connect}.\\"" -DAUTH="\\"={auth}.\\""'
        opt["buildserv"] = True
        

    key = opt["key"]
    res = opt["resource"]
    qtype = opt["qtype"]

    buildserv = opt["buildserv"]
    
    defines = f'-DDNS2TCP_KEY=\"\\\"{key}\\\"\" -DDNS2TCP_RES=\"\\\"{res}\\\"\" -DDNS2TCP_QUERY_FUNC=\"\\\"{qtype}\\\"\" {obf_str} '

    
            
    cmd = f"cd  tuns/dns2tcp; ./configure  CFLAGS='{defines}'"
    if run_cmd(cmd):
        print("[-] failed configuration")
        
    cmd = "cd tuns/dns2tcp; git apply ../patchs/patch_dns2tcp.patch;"
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
        cmd = "cd tuns/dns2tcp; make clean; gcc common/debug.c -c -o server/debug.o; cd server; make; gcc -Wall -Wunused -o dns2tcpd hmac_sha1.o crc16.o rr.o mycrypto.o session.o queue.o config.o myrand.o auth.o requests.o server.o list.o dns.o dns_decode.o mystrnlen.o memdump.o base64.o socket.o options.o main.o debug.o -static"
        if run_cmd(cmd):
            print("[-] Failed to build server.")
            sys.exit(-1)
        else:
            print("[+] Server has been built.")
            os.replace("tuns/dns2tcp/server/dns2tcpd", "build/dns2tcpd")
    return 
            
def icmp(opt):
    print("[*] Building ICMP Tunnel...")
    _clean()
    cmd = "cd tuns/icmptunnel/; make clean && git apply ../patchs/patch_icmptunnel.patch;"
    run_cmd(cmd)

    raw = opt["raw_sock"]
    buildserv = opt["buildserv"]
    
            
    raw = "-DNO_ROOT" if not raw else ""
        
    cmd = f"cd tuns/icmptunnel && gcc client.c icmp.c tunnel.c {raw}  -c;"
    if run_cmd(cmd):
        print("[-] Failed to compile icmptunnel, check for missing value")    
    cmd = "cd tuns/icmptunnel; ar rcs ../../build/libtun.a client.o icmp.o tunnel.o";    

    if run_cmd(cmd) or not os.path.exists("build/libtun.a"):
        print("[-] Failed building icmptunnel lib.")
        sys.exit(-1)
    
    if buildserv:
        cmd = f"cd tuns/icmptunnel && make clean && gcc icmptunnel.c icmp.c tunnel.c -static -o icmptunnel"
        if not run_cmd(cmd) and os.path.exists("tuns/icmptunnel/icmptunnel"):
            os.replace("tuns/icmptunnel/icmptunnel", "build/icmptunnel")
            print("[+] ICMPTunnel server has been built.")
            
        else:
            print("[-] Failed to build icmptunnel server")
            sys.exit(-1)
    print("[+] Build successfull")


        
def sock(opt):
    print("[+] Building Sock Tunnel...")
    _clean()

    print(f"\t--> Building socket support with dynamic env mode")         
    cmd = f"cd tuns/sock/; rm -f sock.o; gcc sock.c -c -o sock.o;"
    
    if run_cmd(cmd):
        print("[-] Fail compiling.")

    cmd = "cd tuns/sock/; ar rcs ../../build/libtun.a sock.o"
    if run_cmd(cmd) or not os.path.exists("build/libtun.a"):
        print("[-] Failed building sock lib.")
        sys.exit(-1)
    else:
        print("[+] Build successfull")



    
def proxysock(opt):
    print("[*] Building proxysock tunnel...")
    _clean()
    
    cmd = f"cd tuns/proxysocket/; rm -rf tunnel.o proxysock.o;  git apply ../patchs/patch_proxysocket.patch;"
    if run_cmd(cmd):
        print("[-] Failed to apply patchs")
        
    cmd = f"cd tuns/proxysocket; gcc  -Iinclude/ -Isrc/ examples/tunnel.c -c -o tunnel.o && gcc -Isrc/ -Iinclude/ src/proxysocket.c -c -o proxysock.o"
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
    targets = opt["targets"]
    key = opt["key"]
    path_fd = opt["path_fd"] 

    cmd = f"cd tuns/http_enc/;rm -f demux.o; gcc -DFIFO_IN='\"{path_fd}_in\"' -DFIFO_OUT='\"{path_fd}_out\"' -c -o demux.o demux.c"
    if run_cmd(cmd):
        print("[-] Failed to build")

    if key == None:
        print("[+] No key specified, generating one:")
        key = ''.join(random.choice(key_charset) for i in range(24))
        print("\t-> Using : "+key)
    with open("keys/webshell.txt", "w") as k:
        k.write(key)

    for target in targets:
        print(f"[+] Generating target script for {target}")
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


def combiner(tunnels):
    print("[+] Building combined tunnels")
    env = False
    avail_tun = []
    for t in tunnels:

        if tunnels[t]["enabled"]:
            fct = getattr(tuns.builder,t, None)
            fct(tunnels[t])
            cmd = f"objcopy  --redefine-sym tun=tun_{t} build/libtun.a build/libtun_{t}.a"
            if run_cmd(cmd)==0:
                avail_tun.append(t)
                os.unlink("build/libtun.a")
                run_cmd(f"cd build; mkdir reloc; ar x libtun_{t}.a; ld -Bsymbolic -relocatable *.o -o reloc/libtun_{t}.o; rm *.o")


    content = ""
    libs = ""
    reloc = ""

    for tunnel in avail_tun:
        content += f'if (strcmp(selected_tun, "{tunnel}")==0) tun_{tunnel}();\n'
        reloc += f"build/reloc/libtun_{tunnel}.o "

    if args.verbose > 2:
        print("[+] Generated combiner file")
    with open("tuns/combined/combiner_template.c", "r") as template:
        with open("tuns/combined/combiner_template_out.c", "w") as out:
            for i in template.readlines():
                i = i.replace("<CONTENT>", content)
                out.write(i)
                if args.verbose > 2:
                    print(i.rstrip())
                
    cmd = f"gcc tuns/combined/combiner_template_out.c -c -o tuns/combined/combiner_template_out.o"
    run_cmd(cmd)
    
    cmd = f"ar rcs build/libtun.a tuns/combined/combiner_template_out.o {reloc}"
    if  run_cmd(cmd) or not os.path.exists("build/libtun.a"):
        print("[-] Failed building combiner lib.")
        sys.exit(-1)
    else:
        print("[+] Build successfull")


