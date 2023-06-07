FROM alpine:latest AS build-stage-0

COPY . build_root
WORKDIR build_root

RUN apk add autoconf gcc make  python3 git automake musl-dev build-base openssh-keygen binutils linux-headers

RUN git submodule init; git submodule update; true
FROM build-stage-0 AS build-stage-1

RUN python builder.py -D  -vvv  --no-musl --compiler gcc --tun combined,tunnels=dns:icmp:sock:proxysock:http_enc,path_fd=/dev/shm/sshim,buildserv -P sshimpanzee -D --shell /bin/sh --force-clean-build

FROM scratch AS export-stage
COPY --from=build-stage-1 /build_root/build/ /build/
COPY --from=build-stage-1 /build_root/keys/ /keys/


