# arkouda-full-stack

## Background

The arkouda-full-stack image starts a one-locale arkouda\_server and provides both jupyter notebook
and ipython interface to Arkouda.

## Building arkouda-full-stack

```
# set env variables
export CHAPEL_SMP_IMAGE=chapel/chapel-gasnet-smp:1.29.0
export ARKOUDA_BRANCH_NAME=2023.02.08
export ARKOUDA_DISTRO_NAME=v2023.02.08
export ARKOUDA_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda/archive/refs/tags/v2023.02.08.zip
export ARKOUDA_IMAGE_REPO=bearsrus

docker build --build-arg CHAPEL_SMP_IMAGE=$CHAPEL_SMP_IMAGE \
             --build-arg ARKOUDA_DISTRO_NAME=$ARKOUDA_DISTRO_NAME \
             --build-arg ARKOUDA_DOWNLOAD_URL=$ARKOUDA_DOWNLOAD_URL \
             --build-arg ARKOUDA_BRANCH_NAME=$ARKOUDA_BRANCH_NAME \
             -f arkouda-full-stack -t $ARKOUDA_IMAGE_REPO/arkouda-full-stack:$ARKOUDA_DISTRO_NAME .
```

## Running arkouda-full-stack

By default arkouda-full-stack launches a jupyter notebook that is accessible via http://$HOSTNAME:8888

### Basic Configuration

```
# set env variables
export ARKOUDA_IMAGE_REPO=bearsrus
export ARKOUDA_VERSION=v2023.02.08

docker run -it --rm -p 8888:8888 $ARKOUDA_IMAGE_REPO/arkouda-full-stack:$ARKOUDA_VERSION
```

### Mount Directory

To mount a directory containing files to be analyzed, execute the following command:

```
# set env variables
export ARKOUDA_IMAGE_REPO=bearsrus
export ARKOUDA_VERSION=v2023.02.08
export HOST_DIR=/opt/datafiles
export CONTAINER_DIR=/app/data

docker run -it --rm -p 8888:8888 --mount type=bind,source=$HOST_DIR,target=$CONTAINER_DIR \
                    $ARKOUDA_IMAGE_REPO/arkouda-full-stack:$ARKOUDA_VERSION
```

#### Launch with ipython Interface

If preferred, arkouda-full-stack also enables an ipython interface to Arkouda. The corresponding docker launch
command is as follows:

```
# set env variables
export ARKOUDA_IMAGE_REPO=bearsrus
export ARKOUDA_VERSION=v2023.02.08

docker run -it --rm --entrypoint=/opt/start-arkouda-full-stack.sh \
                    $ARKOUDA_IMAGE_REPO/arkouda-full-stack:$ARKOUDA_VERSION
```

# arkouda-smp-server

## Background

The arkouda-smp-server extends chapel-gasnet-smp to deliver a GASNET smp configuration that enables 
1..n Chapel locales within a single docker container.

## Building arkouda-smp-server

```
export CHAPEL_SMP_IMAGE=chapel/chapel-gasnet-smp:1.29.0
export ARKOUDA_DISTRO_NAME=v2023.02.08
export ARKOUDA_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda/archive/refs/tags/v2023.02.08.zip
export ARKOUDA_BRANCH_NAME=2023.02.08
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
export ARKOUDA_VERSION=v2023.02.08

docker run -it --rm -p 5555:5555 $ARKOUDA_IMAGE_REPO/arkouda-smp-server:$ARKOUDA_VERSION
```

# chapel-gasnet-udp

## Background

While arkouda-smp-server extends [chapel-gasnet-smp](https://hub.docker.com/r/chapel/chapel-gasnet-smp), there is 
no corresponding chapel-gasnet-udp image. Accordingly, the chapel-gasnet-udp image provide a base for arkouda-udp-server

While arkouda-smp-server extends [chapel-gasnet-smp](https://hub.docker.com/r/chapel/chapel-gasnet-smp), there is 
no corresponding chapel-gasnet-udp image. chapel-gasnet-udp is a Chapel base image that enables gasnet/udp comms 
across 1..n locales. Accordingly, the chapel-gasnet-udp image provides a base image for the arkouda-udp-server.

## Building chapel-gasnet-udp

```
export CHPL_BASE_IMAGE=ubuntu:22.04
export CHPL_VERSION=1.29.0
export CHAPEL_UDP_IMAGE_REPO=bearsrus

docker build --build-arg CHPL_BASE_IMAGE=$CHPL_BASE_IMAGE --build-arg CHPL_VERSION=$CHPL_VERSION -f chapel-gasnet-udp -t $CHAPEL_UDP_IMAGE_REPO/chapel-gasnet-udp:$CHPL_VERSION .
```

# arkouda-udp-server

## Background

The arkouda-udp-server image delivers a GASNET udp configuration that enables deployment of multi-locale Arkouda across 1..n machines that communicate via GASNET/udp.

## Building arkouda-udp-server

```
export CHAPEL_UDP_IMAGE=bearsrus/chapel-gasnet-udp:1.29.0
export ARKOUDA_DISTRO_NAME=v2023.02.08
export ARKOUDA_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda/archive/refs/tags/v2023.02.08.zip
export ARKOUDA_BRANCH_NAME=2023.02.08
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

## Launching arkouda-udp-server

The arkouda-udp-server docker image is designed to be launched on Kubernetes via Helm. The Arkouda-on-Kubernetes deployment will be added to arkouda-contrib in the near future.

# Building Images with Python script

## Background

The [build_docker_image.py](./build_docker_image.py) python script is a convenient means of building all for arkouda-docker images. 

## Python Docker build script

The --help command displays the docker build parameters:

```
python build_docker_image.py --help
usage: build_docker_image.py [-h] [--image_type IMAGE_TYPE] [--arkouda_tag ARKOUDA_TAG] [--arkouda_branch ARKOUDA_BRANCH] [--dockerhub_repo DOCKERHUB_REPO]
                             [--arkouda_repo ARKOUDA_REPO] [--chapel_version CHAPEL_VERSION]

Build bearsrus docker images

optional arguments:
  -h, --help            show this help message and exit
  --image_type IMAGE_TYPE
                        possible image types are ARKOUDA_FULL_STACK, ARKOUDA_SMP_SERVER, ARKOUDA_UDP_SERVER and CHAPEL_UDP
  --arkouda_tag ARKOUDA_TAG
                        if the desired arkouda version is a tag
  --arkouda_branch ARKOUDA_BRANCH
                        if the desired arkouda version is a branch
  --dockerhub_repo DOCKERHUB_REPO
                        the dockerhub repo the image is to be published, defaults to bearsrus
  --arkouda_repo ARKOUDA_REPO
                        the arkouda repo containing the arkouda source code, defaults to Bears-R-Us
  --chapel_version CHAPEL_VERSION
                        Version of Chapel used to build image
``` 

## Example Build Commands

### arkouda-full-stack

```
python build_docker_image.py --arkouda_tag=v2023.02.08 --chapel_version=1.29.0 --image_type=ARKOUDA_FULL_STACK
```

### arkouda-smp-server

```
python build_docker_image.py --arkouda_tag=v2023.02.08 --chapel_version=1.29.0 --image_type=ARKOUDA_SMP_SERVER
```

### chapel-gasnet-udp

```
python build_docker_image.py --chapel_version=1.29.0 --image_type=CHAPEL_UDP
```

### arkouda-udp-server

```
python build_docker_image.py --arkouda_tag=v2023.02.08 --chapel_version=1.29.0 --image_type=ARKOUDA_UDP_SERVER
```


