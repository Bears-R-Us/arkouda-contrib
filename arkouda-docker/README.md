# arkouda-full-stack

## Building arkouda-full-stack

```
# set env variables
ARKOUDA_BRANCH_NAME=2022.10.13
ARKOUDA_DISTRO_NAME=v2022.10.13
ARKOUDA_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda/archive/refs/tags/v2022.10.13.zip

docker build --build-arg ARKOUDA_DISTRO_NAME=$ARKOUDA_DISTRO_NAME --build-arg ARKOUDA_DOWNLOAD_URL=$ARKOUDA_DOWNLOAD_URL --build-arg ARKOUDA_BRANCH_NAME=$ARKOUDA_BRANCH_NAME -f arkouda-full-stack -t hokiegeek2/arkouda-full-stack:$ARKOUDA_DISTRO_NAME .
```

## Running arkouda-full-stack

```
docker run -it --rm -p 8888:8888 hokiegeek2/arkouda-full-stack:v20221013
```

# arkouda-smp-server

## Building arkouda-smp-server

```
docker build --build-arg ARKOUDA_DISTRO_NAME=$ARKOUDA_DISTRO_NAME --build-arg ARKOUDA_DOWNLOAD_URL=$ARKOUDA_DOWNLOAD_URL --build-arg ARKOUDA_BRANCH_NAME=$ARKOUDA_BRANCH_NAME -f arkouda-smp-server -t hokiegeek2/arkouda-smp-server:v20221013 
```

## Running arkouda-smp-server

```
docker run -it --rm -p 5555:5555 hokiegeek2/arkouda-smp-server:v20221013
```