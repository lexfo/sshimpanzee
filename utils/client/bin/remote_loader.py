#/bin/python

import subprocess
from subprocess import Popen, PIPE
import argparse
import os
import time
import select
import sys
import fcntl

parser = argparse.ArgumentParser(description='Remote loader')
parser.add_argument('ssh_socket',
                    help='Path to ssh socket')


parser.add_argument('client',
                    help='path to the client executable file and arguments, use "-" for stdin/stdout')


parser.add_argument('server',
                    help='path to the server executable file')

parser.add_argument('arguments', help='Argument to the remote executable', default=[], nargs='*')


args = parser.parse_args()
arguments = " ".join(args.arguments)

stat = os.stat(args.server)
print(f"[*] Running \"{args.server} {arguments}\" on remote server ...")
ssh_command = f"ssh -S {args.ssh_socket} . -s remote-exec"
print(f"[+] Using socket @ {args.ssh_socket} (cmdline: {ssh_command})")

env = os.environ.copy()
process = Popen(ssh_command, stdin=PIPE, stdout=PIPE, stderr=None, shell=True, env=env)

b = f"{args.server} ".encode()
x = process.stdout.read(26)
process.stdin.write(b)
try:
    process.stdin.flush() 
except:
    while(True):
        x = process.stderr.readline()
        if not x:
            break
        else :
            print(x)
        
b = f"{stat.st_size}".encode()
process.stdin.write(b)
try:
    process.stdin.flush() 
except:
    print(process.stderr.readline())


if len(arguments) != 0:
    arguments += " "

b = f" {arguments}\n".encode()
process.stdin.write(b)
try:
    process.stdin.flush() 
except:
    print(process.stderr.readline())

time.sleep(1)
print("[+] Starting file transfer")
with open(args.server, "rb") as f:
    while True:
        chunk = f.read()
        process.stdin.write(chunk)
        if not chunk:
            break
        
    print("[+] File has been transfered, running it")
try:
    process.stdin.flush() 
except:
    pass

if args.client != "-":
    process_client = Popen(args.client, stdin=PIPE, stdout=PIPE, stderr=None, shell=True, env=env)
    stdout = process_client.stdout
    stdin = process_client.stdin
else:
    stdout = sys.stdin.buffer
    stdin = sys.stdout.buffer

inputs  = [ process.stdout, stdout ]
outputs = []


orig_fl = fcntl.fcntl(process.stdout, fcntl.F_GETFL)
fcntl.fcntl(process.stdout, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)
orig_fl_cli = fcntl.fcntl(stdout, fcntl.F_GETFL)
fcntl.fcntl(stdout, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)


c = True
while c:
    readable, writable, exceptional = select.select(inputs, outputs, inputs)
    for i in readable:
        if i == process.stdout:
            x = i.read()
            stdin.write(x)
            stdin.flush()
            if not x:
                c = False
        elif i == stdout:
            x = i.read()
            process.stdin.write(x)
            process.stdin.flush()
            if not x:
                c = False
