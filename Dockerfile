FROM alpine:latest AS build-stage-0

COPY . build_root
WORKDIR build_root

RUN apk add autoconf gcc make  python3 git automake musl-dev build-base openssh-keygen binutils linux-headers py3-yaml

RUN git submodule init; git submodule update; true
FROM build-stage-0 AS build-stage-1

RUN mkdir -p /build_root/build/
RUN python builder.py -c build.yaml 2>&1 | tee /build_root/build/build.log

FROM scratch AS export-stage
COPY --from=build-stage-1 /build_root/build/ /build/
COPY --from=build-stage-1 /build_root/keys/ /keys/


