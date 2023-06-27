# arkouda-docker

The arkouda-docker project delivers Chapel and Arkouda docker images that enable containerized Arkouda to be deployed on Kubernetes, Slurm >= 21.08.5, and bare metal.  

# arkouda-full-stack

## Background

The arkouda-full-stack image starts a one-locale arkouda\_server and provides both jupyter notebook
and ipython interface to Arkouda. The arkouda-full-stack image extends bearsrus/chapel-gasnet-smp.

## Building arkouda-full-stack

```
# set env variables
export CHAPEL_SMP_IMAGE=bearsrus/chapel-gasnet-smp:1.30.0
export ARKOUDA_BRANCH_NAME=2023.06.16
export ARKOUDA_DISTRO_NAME=v2023.06.16
export ARKOUDA_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda/archive/refs/tags/v2023.06.16.zip
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
export ARKOUDA_VERSION=v2023.06.16

docker run -it --rm -p 8888:8888 $ARKOUDA_IMAGE_REPO/arkouda-full-stack:$ARKOUDA_VERSION
```

### Mount Directory

To mount a directory containing files to be analyzed, execute the following command:

```
# set env variables
export ARKOUDA_IMAGE_REPO=bearsrus
export ARKOUDA_VERSION=v2023.06.16
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
export ARKOUDA_VERSION=v2023.06.16

docker run -it --rm -p 8888:8888 --entrypoint=/opt/arkouda/start-smp-arkouda-full-stack.sh \
                    $ARKOUDA_IMAGE_REPO/arkouda-full-stack:$ARKOUDA_VERSION
```

# arkouda-smp-server

## Background

The arkouda-smp-server extends bearsrus/chapel-gasnet-smp to deliver a GASNET smp configuration that enables 
1..n Chapel locales within a single docker container.

## Building arkouda-smp-server

```
export CHAPEL_SMP_IMAGE=bearsrus/chapel-gasnet-smp:1.30.0
export ARKOUDA_DISTRO_NAME=v2023.06.16
export ARKOUDA_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda/archive/refs/tags/v2023.06.16.zip
export ARKOUDA_BRANCH_NAME=2023.06.16
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
export ARKOUDA_VERSION=v2023.06.16

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
export CHPL_VERSION=1.30.0
export CHAPEL_UDP_IMAGE_REPO=bearsrus

docker build --build-arg CHPL_BASE_IMAGE=$CHPL_BASE_IMAGE --build-arg CHPL_VERSION=$CHPL_VERSION -f chapel-gasnet-udp -t $CHAPEL_UDP_IMAGE_REPO/chapel-gasnet-udp:$CHPL_VERSION .
```

# arkouda-udp-server

## Background

The arkouda-udp-server image extends bearsrus/chapel-gasnet-udp to deliver a GASNET udp configuration that enables deployment of multi-locale Arkouda across 1..n machines that communicate via GASNET/udp.

## Building arkouda-udp-server

```
export CHAPEL_UDP_IMAGE=bearsrus/chapel-gasnet-udp:1.30.0
export ARKOUDA_DISTRO_NAME=v2023.06.16
export ARKOUDA_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda/archive/refs/tags/v2023.06.16.zip
export ARKOUDA_BRANCH_NAME=2023.06.16
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

The arkouda-udp-server docker image is designed to be launched on Kubernetes via the bears-r-us [Helm charts](../arkouda-helm-charts).

# prometheus-arkouda-exporter

## Background

The prometheus-arkouda-exporter Docker image encapsulates the Arkouda prometheus exporter, enabling it to be deployed on Kubernetes, on Slurm, or via Docker Compose.

## Building prometheus-arkouda-exporter

There are six build arguments passed in to the docker build command:

1. EXPORTER\_VERSION: it is recommended that this coincide with the Arkouda tag version
2. ARKOUDA\_DISTRO\_NAME: corresponds to the Arkouda tag or branch name
3. ARKOUDA\_BRANCH\_NAME: matches the ARKOUDA\_DISTRO\_NAME if the Arkouda distro is a branch, is the ARKOUDA\_DISTRO\_NAME w/out "v" if the Arkouda distro is a tag
4. ARKOUDA\_DOWNLOAD\_URL: the url for the Arkouda source code zip file that corresponds to the ARKOUDA\_DISTRO\_NAME
5. ARKOUDA\_CONTRIB\_DOWNLOAD\_URL: arkouda-contrib project download url
6. ARKOUDA\_CONTRIB\_DISTRO\_NAME: corresponds to the arkouda-contrib branch name

An example docker build command sequence is as follows:

```
export EXPORTER_VERSION=v2023.06.16
export ARKOUDA_DISTRO_NAME=v2023.06.16
export ARKOUDA_BRANCH_NAME=2023.06.16
export ARKOUDA_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda/archive/refs/tags/v2023.06.16.zip
export ARKOUDA_CONTRIB_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda-contrib/archive/refs/heads/main.zip
export ARKOUDA_CONTRIB_DISTRO_NAME=main

docker build --build-arg ARKOUDA_DISTRO_NAME=$ARKOUDA_DISTRO_NAME --build-arg ARKOUDA_BRANCH_NAME=$ARKOUDA_BRANCH_NAME --build-arg ARKOUDA_DOWNLOAD_URL=$ARKOUDA_DOWNLOAD_URL --build-arg ARKOUDA_CONTRIB_DOWNLOAD_URL=$ARKOUDA_CONTRIB_DOWNLOAD_URL --build-arg ARKOUDA_CONTRIB_DISTRO_NAME=$ARKOUDA_CONTRIB_DISTRO_NAME -f prometheus-arkouda-exporter -t bearsrus/prometheus-arkouda-exporter:$EXPORTER_VERSION .
```

## Running prometheus-arkouda-exporter

```
export EXPORTER_VERSION=v2023.06.16

docker run -e ARKOUDA_METRICS_SERVICE_NAME=localhost -e ARKOUDA_METRICS_SERVICE_PORT=5556 -e POLLING_INTERVAL_SECONDS=5 -e EXPORT_PORT=5080 -e EXPORT_PORT=5080 -p 5080:5080 bearsrus/prometheus-arkouda-exporter:$EXPORTER_VERSION
```

# arkouda-smp-developer

## Background

The arkouda-smp-developer image enables Arkouda developers to mount whichever directories they are working in (arkouda for Python, src for Chapel) to the arkouda-smp-developer docker container and be able to develop, build, and test within a pre-built Chapel and Arkouda dependencies stack. Since the GASNET\_COMM\_SUBSTRATE is smp, the developer can execute multi-locale Arkouda testing with the arkouda-smp-developer container. 

## Building arkouda-smp-developer Image

The arkouda-smp-developer Docker build sequence is very similar to the arkouda-smp-server build sequence, an example of which is shown below:

```
export CHAPEL_SMP_IMAGE=bearsrus/chapel-gasnet-smp:1.30.0
export ARKOUDA_BRANCH_NAME=2023.06.16
export ARKOUDA_DISTRO_NAME=v2023.06.16
export ARKOUDA_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda/archive/refs/tags/v2023.06.16.zip
export ARKOUDA_IMAGE_REPO=bearsrus

docker build --build-arg CHAPEL_SMP_IMAGE=$CHAPEL_SMP_IMAGE \
             --build-arg ARKOUDA_DISTRO_NAME=$ARKOUDA_DISTRO_NAME \
             --build-arg ARKOUDA_DOWNLOAD_URL=$ARKOUDA_DOWNLOAD_URL \
             --build-arg ARKOUDA_BRANCH_NAME=$ARKOUDA_BRANCH_NAME \
             -f arkouda-smp-developer -t $ARKOUDA_IMAGE_REPO/arkouda-smp-developer:$ARKOUDA_DISTRO_NAME .
```

## Running arkouda-smp-developer

Running arkouda-smp-developer with a directory mounted enables building, testing, and running Arkouda in GASNET smp mode within a Docker container. An example docker run command is shown below, where arkouda-smp-developer Docker container is launched from the Arkouda project root directory and the Chapel src directory is mounted:

```
# set env variables
export ARKOUDA_IMAGE_REPO=bearsrus
export ARKOUDA_VERSION=v2023.06.16

docker run -it --rm -v $PWD/src:/opt/arkouda/src bearsrus/arkouda-smp-developer:v2023.06.16 
```

Once the arkouda-smp-developer Docker container is started, any changes to the files within the mounted directory are permanent and retained 
after the Docker container is stopped. In the above example, the developer writes Chapel code and tests within the arkouda-smp-developer Docker 
container. Once development is complete, the Docker container can be stopped and the updated Chapel files are ready for further development, 
commit and check-in to github, etc...

# Building Images with Python script

## Background

The [build_docker_image.py](./build_docker_image.py) python script is a convenient means of building the arkouda-docker images. 

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

Shown below are example build commands. To ensure the optimal, respective performance profile and feature sets of Chapel and Arkouda are leveraged, build the chapel-gasnet-udp image with the latest version of Chapel and all Arkouda images with the latest Arkouda tag. 

### arkouda-full-stack

```
python build_docker_image.py --arkouda_tag=v2023.06.16 --chapel_version=1.30.0 --image_type=arkouda-full-stack
```

### chapel-gasnet-smp

```
python build_docker_image.py --chapel_version=1.30.0 --image_type=chapel-gasnet-smp
```

### arkouda-smp-server

```
python build_docker_image.py --arkouda_tag=v2023.06.16 --chapel_version=1.30.0 --image_type=arkouda-smp-server
```

### chapel-gasnet-udp

```
python build_docker_image.py --chapel_version=1.30.0 --image_type=chapel-gasnet-udp
```

### arkouda-udp-server

```
python build_docker_image.py --arkouda_tag=v2023.06.16 --chapel_version=1.30.0 --image_type=arkouda-udp-server
```

### prometheus-arkouda-exporter

```
python build_docker_image.py --arkouda_tag=v2023.06.16 --image_type=prometheus-arkouda-exporter
```

### arkouda-smp-developer

```
python build_docker_image.py --arkouda_tag=v2023.06.16 --chapel_version=1.30.0 --image_type=arkouda-smp-developer
```
