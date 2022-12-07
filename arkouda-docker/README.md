# arkouda-full-stack

## Background

The arkouda-full-stack image starts a one-locale arkouda\_server and provides an ipython interface to Arkouda.

## Building arkouda-full-stack

```
# set env variables
export CHAPEL_SMP_IMAGE=chapel/chapel-gasnet-smp:1.28.0
export ARKOUDA_BRANCH_NAME=2022.11.17
export ARKOUDA_DISTRO_NAME=v2022.11.17
export ARKOUDA_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda/archive/refs/tags/v2022.11.17.zip
export ARKOUDA_IMAGE_REPO=bearsrus

docker build --build-arg CHAPEL_SMP_IMAGE=$CHAPEL_SMP_IMAGE \
             --build-arg ARKOUDA_DISTRO_NAME=$ARKOUDA_DISTRO_NAME \
             --build-arg ARKOUDA_DOWNLOAD_URL=$ARKOUDA_DOWNLOAD_URL \
             --build-arg ARKOUDA_BRANCH_NAME=$ARKOUDA_BRANCH_NAME \
             -f arkouda-full-stack -t $ARKOUDA_IMAGE_REPO/arkouda-full-stack:$ARKOUDA_DISTRO_NAME .
```

## Running arkouda-full-stack

```
# set env variables
export ARKOUDA_IMAGE_REPO=bearsrus
export ARKOUDA_VERSION=v2022.11.17

docker run -it --rm -p 8888:8888 $ARKOUDA_IMAGE_REPO/arkouda-full-stack:$ARKOUDA_VERSION
```

# arkouda-smp-server

## Background

The arkouda-smp-server extends chapel-gasnet-smp to deliver a GASNET smp configuration that enables 1..n Chapel locales within a single docker container.

## Building arkouda-smp-server

```
export CHAPEL_SMP_IMAGE=chapel/chapel-gasnet-smp:1.28.0
export ARKOUDA_DISTRO_NAME=v2022.11.17
export ARKOUDA_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda/archive/refs/tags/v2022.11.17.zip
export ARKOUDA_BRANCH_NAME=2022.11.17
export ARKOUDA_IMAGE_REPO=bearsrus

docker build --build-arg CHAPEL_SMP_IMAGE=$CHAPEL_SMP_IMAGE \
             --build-arg ARKOUDA_DISTRO_NAME=$ARKOUDA_DISTRO_NAME \
             --build-arg ARKOUDA_DOWNLOAD_URL=$ARKOUDA_DOWNLOAD_URL \
             --build-arg ARKOUDA_BRANCH_NAME=$ARKOUDA_BRANCH_NAME \
             -f arkouda-smp-server -t $ARKOUDA_IMAGE_REPO/arkouda-smp-server:$ARKOUDA_DISTRO_NAME .
```

## Running arkouda-smp-server

```
# set env variables
export ARKOUDA_IMAGE_REPO=bearsrus
export ARKOUDA_VERSION=v2022.11.17

docker run -it --rm -p 5555:5555 $ARKOUDA_IMAGE_REPO/arkouda-smp-server:$ARKOUDA_VERSION
```

# chapel-gasnet-udp

## Background

While arkouda-smp-server extends [chapel-gasnet-smp](https://hub.docker.com/r/chapel/chapel-gasnet-smp), there is no corresponding chapel-gasnet-udp image. Accordingly, the chapel-gasnet-udp image provide a base for arkouda-udp-server

While arkouda-smp-server extends [chapel-gasnet-smp](https://hub.docker.com/r/chapel/chapel-gasnet-smp), there is no corresponding chapel-gasnet-udp image. chapel-gasnet-udp is a Chapel base image that enables gasnet/udp comms across 1..n locales. Accordingly, the chapel-gasnet-udp image provides a base image for the arkouda-udp-server.

## Building chapel-gasnet-udp

```
export CHPL_BASE_IMAGE=ubuntu:22.04
export CHPL_VERSION=1.28.0
export CHAPEL_UDP_IMAGE_REPO=bearsrus

docker build --build-arg CHPL_BASE_IMAGE=$CHPL_BASE_IMAGE --build-arg CHPL_VERSION=$CHPL_VERSION -f chapel-gasnet-udp -t $CHAPEL_UDP_IMAGE_REPO/chapel-gasnet-udp:$CHPL_VERSION .
```

# arkouda-udp-server

## Background

The arkouda-udp-server image delivers a GASNET udp configuration that enables deployment of multi-locale Arkouda across 1..n machines that communicate via GASNET/udp.

## Building arkouda-udp-server

```
export CHAPEL_UDP_IMAGE=bearsrus/chapel-gasnet-udp:1.28.0
export ARKOUDA_DISTRO_NAME=v2022.11.17
export ARKOUDA_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda/archive/refs/tags/v2022.11.17.zip
export ARKOUDA_BRANCH_NAME=2022.11.17
export ARKOUDA_INTEGRATION_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda-contrib/archive/refs/heads/main.zip
export ARKOUDA_INTEGRATION_DISTRO_NAME=main
export ARKOUDA_IMAGE_REPO=bearsrus

docker build --build-arg CHAPEL_UDP_IMAGE=$CHAPEL_UDP_IMAGE \
             --build-arg ARKOUDA_DISTRO_NAME=$ARKOUDA_DISTRO_NAME \
             --build-arg ARKOUDA_DOWNLOAD_URL=$ARKOUDA_DOWNLOAD_URL \
             --build-arg ARKOUDA_INTEGRATION_DISTRO_NAME=$ARKOUDA_INTEGRATION_DISTRO_NAME \
             --build-arg ARKOUDA_BRANCH_NAME=$ARKOUDA_BRANCH_NAME \
             --build-arg ARKOUDA_INTEGRATION_DOWNLOAD_URL=$ARKOUDA_INTEGRATION_DOWNLOAD_URL \
             -f arkouda-udp-server -t $ARKOUDA_IMAGE_REPO/arkouda-udp-server:$ARKOUDA_DISTRO_NAME .
```
