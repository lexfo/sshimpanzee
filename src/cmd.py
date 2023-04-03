from src.args import args
import os

def run_cmd(cmd):
    if args.verbose>0:
        print("|=> $ " + cmd)
    if not args.verbose > 1:
        cmd = "(" + cmd + ")  > /dev/null  2>&1"
    return os.system(cmd)
