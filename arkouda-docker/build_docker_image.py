#!/usr/bin/env python3

import argparse, enum, subprocess, sys
from typing import Optional
from enum import Enum

class ImageType(Enum):
    '''
    The ImageType enum provides controlled vocabulary for the docker image type
    '''
    ARKOUDA_FULL_STACK = 'arkouda-full-stack'
    ARKOUDA_SMP_SERVER = 'arkouda-smp-server'
    ARKOUDA_UDP_SERVER = 'arkouda-udp-server'
    ARKOUDA_IBV_SERVER = 'arkouda-ibv-server'
    CHAPEL_GASNET_UDP = 'chapel-gasnet-udp'
    CHAPEL_GASNET_IBV = 'chapel-gasnet-ibv'
    PROMETHEUS_ARKOUDA_EXPORTER = 'prometheus-arkouda-exporter'
    ARKOUDA_SMP_DEVELOPER = 'arkouda-smp-developer'

def getImageFile(imageType: ImageType) -> str:
    '''
    Returns the Dockerfile per the image type

    :param ImageType imageType: Docker image type enum    
    :return: Dockerfile corresponding to the image type
    :rtype: str
    '''
    return imageType.value

def getDistro(tag: str) -> str:
    '''
    Returns the distro name corresponding to the Arkouda tag

    :param str tag: Arkouda tag
    :return: distro name 
    :rtype: str
    '''
    return tag.lstrip('v')

def buildImage(dockerRepo: str, chapelVersion: str, file: str, distro: str, tag: Optional[str], multiarch: bool, concurrency: int, push: bool) -> None:
    '''
    Generates a build tag and then builds the desired docker image

    :param str dockerRepo: dockerhub repo the image will be published to
    :param str chapelVersion: version of Chapel used to build Arkouda server
    :param str file: Dockerfile name
    :param str distro: Arkouda distro (branch name)
    :param Optional[str] tag: Arkouda tag name, if applicable
    :param bool multiarch: whether to build a multiarch image
    :param int concurrency: number of make jobs to run in parallel
    :param bool push: whether to push the image to dockerhub after building
    :return: None
    '''


    def buildImageHelper(build_args: dict) -> None:
        use_tag = tag
        if not tag and build_args['CHPL_VERSION']:
            use_tag = build_args['CHPL_VERSION']
        docker_tag = generateBuildTag(dockerRepo=dockerRepo,file=file,tag=use_tag,distro=distro)
        print(f'Building docker image {docker_tag} using Dockerfile {file}')
        args = ['docker', 'build']
        for key, value in build_args.items():
            args.append('--build-arg')
            args.append(f'{key}={value}')
        args.extend(['--build-arg', f'MAKE_THREADS={concurrency}'])
        if multiarch:
            args.extend(['--platform', 'linux/amd64,linux/arm64'])
        if push:
            args.extend(['--push'])
        args.extend(['-f', file, '-t', docker_tag])
        args.append('.')
        print("Running docker build command: ", ' '.join(args))
        result = subprocess.run(args, stdout=subprocess.DEVNULL)
        print(result)


    if file == ImageType.ARKOUDA_FULL_STACK.value:
        buildImageHelper(build_args={
                             'CHAPEL_SMP_IMAGE': generateChplSmpVersion(dockerRepo, chapelVersion),
                             'ARKOUDA_DISTRO_NAME': getDistroName(distro=distro, tag=tag),
                             'ARKOUDA_DOWNLOAD_URL': generateArkoudaDownloadUrl(tag=tag, branch=distro),
                             'ARKOUDA_BRANCH_NAME': distro,
                         }
                        )
    elif file == ImageType.ARKOUDA_SMP_SERVER.value:
        buildImageHelper(build_args={
                             'CHAPEL_SMP_IMAGE': generateChplSmpVersion(dockerRepo, chapelVersion),
                             'ARKOUDA_DISTRO_NAME': getDistroName(distro=distro, tag=tag),
                             'ARKOUDA_DOWNLOAD_URL': generateArkoudaDownloadUrl(tag=tag, branch=distro),
                             'ARKOUDA_BRANCH_NAME': distro,
                         }
                        )
    elif file == ImageType.ARKOUDA_UDP_SERVER.value:
        buildImageHelper(build_args={
                            'CHAPEL_UDP_IMAGE': generateChplUdpVersion(dockerRepo, chapelVersion),
                            'ARKOUDA_DISTRO_NAME': getDistroName(distro=distro, tag=tag),
                            'ARKOUDA_DOWNLOAD_URL': generateArkoudaDownloadUrl(tag=tag, branch=distro),
                            'ARKOUDA_BRANCH_NAME': distro,
                            'ARKOUDA_INTEGRATION_DOWNLOAD_URL': 'https://github.com/Bears-R-Us/arkouda-contrib/archive/refs/heads/main.zip',
                            'ARKOUDA_INTEGRATION_DISTRO_NAME': 'main',
                        }
                        )
    elif file == ImageType.ARKOUDA_IBV_SERVER.value:
        buildImageHelper(build_args={
                            'CHAPEL_IBV_IMAGE': generateChplIbvVersion(dockerRepo, chapelVersion),
                            'ARKOUDA_DISTRO_NAME': getDistroName(distro=distro, tag=tag),
                            'ARKOUDA_DOWNLOAD_URL': generateArkoudaDownloadUrl(tag=tag, branch=distro),
                            'ARKOUDA_BRANCH_NAME': distro,
                            'ARKOUDA_INTEGRATION_DOWNLOAD_URL': 'https://github.com/Bears-R-Us/arkouda-contrib/archive/refs/heads/main.zip',
                            'ARKOUDA_INTEGRATION_DISTRO_NAME': 'main',
                        }
                        )
    elif file == ImageType.CHAPEL_GASNET_UDP.value:
        buildImageHelper(build_args={
                            'CHPL_VERSION': chapelVersion,
                            'CHPL_UDP_IMAGE_REPO': dockerRepo,
                        }
                        )
    elif file == ImageType.CHAPEL_GASNET_IBV.value:
        buildImageHelper(build_args={
                             'CHPL_VERSION': chapelVersion,
                             'CHPL_IBV_IMAGE_REPO': dockerRepo,
                         }
                         )
    elif file == ImageType.PROMETHEUS_ARKOUDA_EXPORTER.value:
        buildImageHelper(build_args={
                            'ARKOUDA_DISTRO_NAME': getDistroName(distro=distro, tag=tag),
                            'ARKOUDA_DOWNLOAD_URL': generateArkoudaDownloadUrl(tag=tag, branch=distro),
                            'ARKOUDA_BRANCH_NAME': distro,
                            'ARKOUDA_CONTRIB_DOWNLOAD_URL': 'https://github.com/Bears-R-Us/arkouda-contrib/archive/refs/heads/main.zip',
                            'ARKOUDA_CONTRIB_DISTRO_NAME': 'main',
                        }
                        )
    elif file == ImageType.ARKOUDA_SMP_DEVELOPER.value:
        buildImageHelper(build_args={
                            'CHAPEL_SMP_IMAGE': generateChplSmpVersion(dockerRepo, chapelVersion),
                            'ARKOUDA_DISTRO_NAME': getDistroName(distro=distro, tag=tag),
                            'ARKOUDA_DOWNLOAD_URL': generateArkoudaDownloadUrl(tag=tag, branch=distro),
                            'ARKOUDA_BRANCH_NAME': distro,
                        }
                        )
    else:
        raise ValueError(f'Dockerfile {file} is invalid, check command-line args')

def getDistroName(distro: str, tag: Optional[str]) -> str:
    '''
    Returns the distro name used to specify the name of the Arkouda distribution that is
    either a tag or a branch.

    :param str distro: name of Arkouda distro (branch)
    :param Optional[str] tag: name of Arkouda tag
    :return: tag or branch name
    :rtype:str
    '''
    return tag if tag else distro

def generateChplSmpVersion(dockerRepo: str, chapelVersion: str) -> str:
    return f'{dockerRepo}/chapel-gasnet-smp:{chapelVersion}'

def generateChplUdpVersion(dockerRepo: str, chapelVersion: str) -> str:
    return f'{dockerRepo}/chapel-gasnet-udp:{chapelVersion}'

def generateChplIbvVersion(dockerRepo: str, chapelVersion: str) -> str:
    return f'{dockerRepo}/chapel-gasnet-ibv:{chapelVersion}'

def generateArkoudaDownloadUrl(tag: Optional[str], branch: Optional[str]) -> str:
    '''
    Generates the Arkouda download URL based upon whether the desired Arkouda version
    is either a tag or a branch.

    :param Optional[str] tag: name of Arkouda tag, if applicable
    :param Optional[str]: name of Arkouda branch, if applicable

    :return: Arkouda download URL
    :rtype: str
    '''
    if tag:
        return f'https://github.com/Bears-R-Us/arkouda/archive/refs/tags/{tag}.zip'
    elif branch:
        return f'https://github.com/Bears-R-Us/arkouda/archive/refs/heads/{branch}.zip'
    else:
        raise ValueError('either the tag or branch must be not None')

def generateBuildTag(dockerRepo: str, file: str, tag: Optional[str], distro: Optional[str]) -> str:
    '''
    Generates a docker build tag corresponding to the repo, file, tag, an distro

    :param str dockerRepo: dockerhub repo the image will be published to
    :param str file: Dockerfile name
    :param Optional[str] tag: Arkouda tag name, if applicable
    :param Optional[str] distro: Arkouda distro (branch name), if applicable

    :return: docker build tag
    :rtype: str
    '''
    base = f'{dockerRepo}/{file}'
    suffix = tag if tag else distro if distro else 'latest'
    return f'{base}:{suffix}'

def buildArkoudaImage(dockerFile: str) -> bool:
    '''
    Returns a boolean indicating if this is an Arkouda image to be built

    :param str dockerFile: name of Dockerfile to be passed to docker build
    :return: boolean indicating if this is an Arkouda Dockerfile
    :rtype: str
    '''
    return 'arkouda' in dockerFile

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Build bearsrus docker images')

    parser.add_argument('--image_type', type=ImageType, required=True,
                        help=f'possible image types are: {", ".join([imageType.value for imageType in ImageType])}')
    parser.add_argument('--arkouda_tag', type=str,
                        help='if the desired arkouda version is a tag')
    parser.add_argument('--arkouda_branch', type=str, 
                        help='if the desired arkouda version is a branch')
    parser.add_argument('--dockerhub_repo', type=str, default='bearsrus',
                        help='the dockerhub repo the image is to be published, defaults to bearsrus')
    parser.add_argument('--arkouda_repo', type=str, default='Bears-R-Us',
                        help='the arkouda repo containing the arkouda source code, defaults to Bears-R-Us')
    parser.add_argument('--chapel_version', type=str,
                        help='Version of Chapel used to build image')
    parser.add_argument('--multiarch', action='store_true',
                        help='Build multiarch image (default native arch only)')
    parser.add_argument('--concurrency', type=int, default=1,
                        help='Number of make jobs to run in parallel (default 1)')
    parser.add_argument('--push', action='store_true',
                        help='Push the image to dockerhub after building (default False)')

    args = parser.parse_args()

    file = getImageFile(args.image_type)
    tag = args.arkouda_tag
    dockerRepo = args.dockerhub_repo
    arkoudaRepo = args.arkouda_repo
    chapelVersion = args.chapel_version
    distro = None
    multiarch = args.multiarch
    concurrency = args.concurrency
    push = args.push

    if buildArkoudaImage(file):
        if tag:
            distro = getDistro(tag)
        else:
            if args.arkouda_branch:
                distro = args.arkouda_branch
            else:
                raise ValueError('Either --arkouda_tag or --arkouda_branch must be specified')

    buildImage(dockerRepo=dockerRepo,chapelVersion=chapelVersion,file=file,tag=tag,distro=distro,multiarch=multiarch,concurrency=concurrency,push=push)
