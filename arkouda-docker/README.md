# arkouda-full-stack

## Background

The arkouda-full-stack image starts a one-locale arkouda_server and provides an ipython interface to Arkouda.

## Building arkouda-full-stack

```
# set env variables
ARKOUDA_BRANCH_NAME=2022.10.13
ARKOUDA_DISTRO_NAME=v2022.10.13
ARKOUDA_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda/archive/refs/tags/v2022.10.13.zip

docker build --build-arg ARKOUDA_DISTRO_NAME=$ARKOUDA_DISTRO_NAME \
             --build-arg ARKOUDA_DOWNLOAD_URL=$ARKOUDA_DOWNLOAD_URL \
             --build-arg ARKOUDA_BRANCH_NAME=$ARKOUDA_BRANCH_NAME \
             -f arkouda-full-stack -t hokiegeek2/arkouda-full-stack:$ARKOUDA_DISTRO_NAME .
```

## Running arkouda-full-stack

```
docker run -it --rm -p 8888:8888 hokiegeek2/arkouda-full-stack:v20221013
```

# arkouda-smp-server

## Background

The arkouda-smp-server extends chapel-gasnet-smp to deliver a GASNET smp configuration that enables 1..n Chapel locales within a single docker container.

## Building arkouda-smp-server

```
export ARKOUDA_DISTRO_NAME=v2022.10.13
export ARKOUDA_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda/archive/refs/tags/v2022.10.13.zip
export ARKOUDA_BRANCH_NAME=2022.10.13

docker build --build-arg ARKOUDA_DISTRO_NAME=$ARKOUDA_DISTRO_NAME \
             --build-arg ARKOUDA_DOWNLOAD_URL=$ARKOUDA_DOWNLOAD_URL \
             --build-arg ARKOUDA_BRANCH_NAME=$ARKOUDA_BRANCH_NAME \
             -f arkouda-smp-server -t hokiegeek2/arkouda-smp-server:$ARKOUDA_DISTRO_NAME 
```

## Running arkouda-smp-server

```
docker run -it --rm -p 5555:5555 hokiegeek2/arkouda-smp-server:v20221013
```

# chapel-gasnet-udp

## Background

While arkouda-smp-server extends [chapel-gasnet-smp](https://hub.docker.com/r/chapel/chapel-gasnet-smp), there is no corresponding chapel-gasnet-udp image. Accordingly, the chapel-gasnet-udp image provide a base for arkouda-udp-server

## Building chapel-gasnet-udp

```
export CHPL_VERSION=1.27.0

docker build --build-arg CHPL_VERSION=$CHPL_VERSION -f chapel-gasnet-udp -t hokiegeek2/chapel-gasnet-udp:$CHPL_VERSION .
```

# arkouda-udp-server

## Background

The arkouda-udp-server image delivers a GASNET udp configuration that enables deployment of multi-locale Arkouda across 1..n machines that communicate via GASNET/udp.

## Building arkouda-udp-server

```
export ARKOUDA_DISTRO_NAME=v2022.10.13
export ARKOUDA_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda/archive/refs/tags/v2022.10.13.zip
export ARKOUDA_BRANCH_NAME=2022.10.13
export ARKOUDA_INTEGRATION_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda-contrib/archive/refs/heads/main.zip
export ARKOUDA_INTEGRATION_DISTRO_NAME=main

docker build --build-arg ARKOUDA_DISTRO_NAME=$ARKOUDA_DISTRO_NAME \
             --build-arg ARKOUDA_DOWNLOAD_URL=$ARKOUDA_DOWNLOAD_URL \
             --build-arg ARKOUDA_INTEGRATION_DISTRO_NAME=$ARKOUDA_INTEGRATION_DISTRO_NAME \
             --build-arg ARKOUDA_BRANCH_NAME=$ARKOUDA_BRANCH_NAME \
             --build-arg ARKOUDA_INTEGRATION_DOWNLOAD_URL=$ARKOUDA_INTEGRATION_DOWNLOAD_URL \
             -f Dockerfile -t hokiegeek2/arkouda-udp-server:$ARKOUDA_DISTRO_NAME .
```
