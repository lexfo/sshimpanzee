import argparse
import textwrap
import yaml
import os
import sys

class ConfigFile:
    def __init__(self,**entries):
        self.__dict__.update(entries)


parser = argparse.ArgumentParser(description='Builder for Reverse SSHD server.', conflict_handler='resolve', formatter_class=argparse.RawDescriptionHelpFormatter, epilog=textwrap.dedent('''Please provide at least a remote address or a tunnel.'''))

### FILE CONFIG
parser.add_argument('--config','-c', dest="config_file", action='store', default=None, help="Path to the yaml build file") 


args = parser.parse_args()

if args.config_file:
    print(f"[+] Building from config file {args.config_file}")
    if not os.path.exists(args.config_file):
        print(f"[-] Config file does not exist.")
        sys.exit(-1)

    with open(args.config_file, "r") as stream:
        try:
            entries = yaml.safe_load(stream)
            args = ConfigFile(**entries)
            
        except yaml.YAMLError as exc:
            print("[-] Failed to parse build file")
            print(exc)
            sys.exit(-1)
