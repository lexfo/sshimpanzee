from src.args import args
from src.cmd import run_cmd
import os

def load_keys():
    print("[*] Loading public key")
    if not (os.path.isfile("keys/HOST") and os.path.isfile("keys/HOST.pub")):
        print("[-] Missing host keys, please regen keys or provide HOST and HOST.pub ssh keys in the keys/ directory.")
        sys.exit(-1)
    with open("keys/HOST") as f:
        host_priv = f.read(1024)
        if(args.verbose > 0):
            print("|=> Private Host Key :\n" + host_priv)
        host_priv = host_priv.replace("\n", "\\n")
        
    with open("keys/HOST.pub") as f:
        host_pub = f.read(1024)
        host_pub = " ".join(host_pub.split(" ")[:2]) + " ROGUE@SERV"
        if(args.verbose > 0):
            print("|=> Public Host Key  :\n" + host_pub)
    if not args.public_key:
        if not os.path.isfile("keys/CLIENT.pub"):
            print("[-] Mission client public key, regenerate key pair or provide a public key (-k)")
            exit(-1)
        with open("keys/CLIENT.pub") as f:
            cli_pub = f.read(1024)
            cli_pub = " ".join(cli_pub.split(" ")[:2]) + " ROGUE@ROGUE"
    else:
        check_type(args.public_key)
        cli_pub = args.public_key

    if(args.verbose > 0):
        print("|=> Public Client Key :\n" + cli_pub)

    return host_priv, host_pub, cli_pub


def gen_keys():
    print("[*] Keys generation...")
    run_cmd("rm -rf keys/; mkdir keys/")
    run_cmd("ssh-keygen -b 4096 -f keys/HOST -t ed25519 -N ''")

    if not args.public_key or (input("[?] You provided a public key, do you want to skip client authentication key generation? (Y/n)") == "n"):
        run_cmd("ssh-keygen -b 4096 -f keys/CLIENT -t ed25519 -N ''")


def check_type(key):
    print("[*] Checking key type...")
    c =  key.split()[0] != "ssh-ed25519"
    if c:    
        print("[-] Key type might not be supported... please provide an ed25519 key.")
    return c


