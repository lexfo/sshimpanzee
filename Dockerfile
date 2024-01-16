FROM alpine:latest AS build-stage-0

RUN apk add autoconf gcc make  python3 git automake musl-dev build-base openssh-keygen binutils linux-headers py3-yaml libtool
COPY builder.py patch_openssh.diff build_root/
COPY openssh-portable build_root/openssh-portable/
COPY src build_root/src/
COPY tuns build_root/tuns/
COPY subsystems build_root/subsystems/
COPY .git build_root/.git/
WORKDIR build_root
RUN git submodule init; git submodule update --force --recursive --init --remote
RUN git -C openssh-portable checkout 8241b9c0529228b4b86d88b1a6076fb9f97e4a99
RUN git -C openssh-portable apply $(pwd)/patch_openssh.diff; 
RUN cd openssh-portable; autoreconf; 

FROM build-stage-0 AS build-stage-1

RUN mkdir -p /build_root/build/
RUN mkdir -p /build_root/keys/

COPY build.yaml /build_root/

RUN python builder.py -c build.yaml 2>&1 | tee /build_root/build/build.log
RUN cp /build_root/openssh-portable/sshd.h /build_root/build/ || true

FROM scratch AS export-stage
COPY --from=build-stage-1 /build_root/build/ /build/
COPY --from=build-stage-1 /build_root/keys/ /keys/


