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
    CHAPEL_GASNET_UDP = 'chapel-gasnet-udp'
    PROMETHEUS_ARKOUDA_EXPORTER = 'prometheus-arkouda-exporter'

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

def buildImage(dockerRepo: str, chapelVersion: str, file: str, distro: str, tag: Optional[str]) -> None:
    '''
    Generates a build tag and then builds the desired docker image

    :param str dockerRepo: dockerhub repo the image will be published to
    :param str chapelVersion: version of Chapel used to build Arkouda server
    :param str file: Dockerfile name
    :param str distro: Arkouda distro (branch name)
    :param Optional[str] tag: Arkouda tag name, if applicable
    :return: None
    '''
    def buildArkoudaFullStack(dockerRepo: str, chapelVersion: str, file: str, dockerTag: str, distro: str, tag: Optional[str]) -> None:
        result = subprocess.run(args=['docker','build',
                                               '--build-arg', f'CHAPEL_SMP_IMAGE={generateChplSmpVersion(chapelVersion)}',
                                               '--build-arg', f'ARKOUDA_DISTRO_NAME={getDistroName(distro=distro, tag=tag)}',
                                               '--build-arg', f'ARKOUDA_DOWNLOAD_URL={generateArkoudaDownloadUrl(tag=tag,branch=distro)}',
                                               '--build-arg', f'ARKOUDA_BRANCH_NAME={distro}',
                                               '-f',file,
                                               '-t', dockerTag, '.'], stdout=subprocess.DEVNULL)
        print(result)

    def buildArkoudaSmpServer(dockerRepo: str, chapelVersion: str, file: str, dockerTag: str, distro: str, tag: Optional[str]) -> None:
        result = subprocess.run(args=['docker','build',
                                               '--build-arg', f'CHAPEL_SMP_IMAGE={generateChplSmpVersion(chapelVersion)}',
                                               '--build-arg', f'ARKOUDA_DISTRO_NAME={getDistroName(distro=distro, tag=tag)}',
                                               '--build-arg', f'ARKOUDA_DOWNLOAD_URL={generateArkoudaDownloadUrl(tag=tag,branch=distro)}',
                                               '--build-arg', f'ARKOUDA_BRANCH_NAME={distro}',
                                               '-f',file,
                                               '-t', dockerTag, '.'], stdout=subprocess.DEVNULL)
        print(result)

    def buildArkoudaUdpServer(dockerRepo: str, chapelVersion: str, file: str, dockerTag: str, distro: str, tag: Optional[str]) -> None:
        result = subprocess.run(args=['docker','build',
                                               '--build-arg', f'CHAPEL_UDP_IMAGE={generateChplUdpVersion(chapelVersion)}',
                                               '--build-arg', f'ARKOUDA_DISTRO_NAME={getDistroName(distro=distro, tag=tag)}',
                                               '--build-arg', f'ARKOUDA_DOWNLOAD_URL={generateArkoudaDownloadUrl(tag=tag,branch=distro)}',
                                               '--build-arg', f'ARKOUDA_BRANCH_NAME={distro}',
                                               '--build-arg', 'ARKOUDA_INTEGRATION_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda-contrib/archive/refs/heads/main.zip',
                                               '--build-arg', 'ARKOUDA_INTEGRATION_DISTRO_NAME=main',
                                               '-f',file,
                                               '-t', dockerTag, '.'], stdout=subprocess.DEVNULL)
        print(result)

    def buildChapelUdp(dockerRepo: str, chapelVersion: str, file: str, dockerTag: str) -> None:
        result = subprocess.run(args=['docker','build',
                                               '--build-arg', f'CHPL_BASE_IMAGE=ubuntu:22.04',
                                               '--build-arg', f'CHPL_VERSION={chapelVersion}',
                                               '--build-arg', f'CHPL_UDP_IMAGE_REPO={dockerRepo}',
                                               '-f',file,
                                               '-t', f'{dockerRepo}/{file}:{chapelVersion}', '.'], stdout=subprocess.DEVNULL)
        print(result)

    def buildPrometheusArkoudaExporter(dockerRepo: str, file: str, dockerTag: str, distro: str, tag: Optional[str]) -> None:
        result = subprocess.run(args=['docker', 'build' ,
                                                '--build-arg', f'ARKOUDA_DISTRO_NAME={getDistroName(distro=distro, tag=tag)}',
                                                '--build-arg', f'ARKOUDA_DOWNLOAD_URL={generateArkoudaDownloadUrl(tag=tag,branch=distro)}',
                                                '--build-arg', f'ARKOUDA_BRANCH_NAME={distro}',
                                                '--build-arg', 'ARKOUDA_CONTRIB_DOWNLOAD_URL=https://github.com/Bears-R-Us/arkouda-contrib/archive/refs/heads/main.zip',
                                                '--build-arg', 'ARKOUDA_CONTRIB_DISTRO_NAME=main',
                                                '-f', file,
                                                '-t', f'{dockerTag}', '.'], stdout=subprocess.DEVNULL)
        print(result)


    dockerTag = generateBuildTag(dockerRepo=dockerRepo, file=file, tag=tag,distro=distro)

    if file == ImageType.ARKOUDA_FULL_STACK.value:
        buildArkoudaFullStack(dockerRepo=dockerRepo,chapelVersion=chapelVersion,file=file,dockerTag=dockerTag,distro=distro,tag=tag)
    elif file == ImageType.ARKOUDA_SMP_SERVER.value:
        buildArkoudaSmpServer(dockerRepo=dockerRepo,chapelVersion=chapelVersion,file=file,dockerTag=dockerTag,distro=distro,tag=tag)
    elif file == ImageType.ARKOUDA_UDP_SERVER.value:
        buildArkoudaUdpServer(dockerRepo=dockerRepo,chapelVersion=chapelVersion,file=file,dockerTag=dockerTag,distro=distro,tag=tag)
    elif file == ImageType.CHAPEL_GASNET_UDP.value:
        buildChapelUdp(dockerRepo=dockerRepo,chapelVersion=chapelVersion,file=file,dockerTag=dockerTag)
    elif file == ImageType.PROMETHEUS_ARKOUDA_EXPORTER.value:
        buildPrometheusArkoudaExporter(dockerRepo=dockerRepo,file=file,distro=distro,dockerTag=dockerTag,tag=tag)
    else:
        raise ValueError(f'docker image type {file} for {ImageType.PROMETHEUS_ARKOUDA_EXPORTER} is invalid')

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

def generateChplSmpVersion(chapelVersion: str) -> str:
    return f'chapel/chapel-gasnet-smp:{chapelVersion}'

def generateChplUdpVersion(chapelVersion: str) -> str:
    return f'bearsrus/chapel-gasnet-udp:{chapelVersion}'

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
    return f'{dockerRepo}/{file}:{tag}' if tag else f'{dockerRepo}/{file}:{distro}'

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

    parser.add_argument('--image_type', type=ImageType,
                        help='possible image types are arkouda_full_stack, arkouda-smp-server, arkouda-udp-server and chapel_udp')
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

    args = parser.parse_args()

    file = getImageFile(args.image_type)
    tag = args.arkouda_tag
    dockerRepo = args.dockerhub_repo
    arkoudaRepo = args.arkouda_repo
    chapelVersion = args.chapel_version
    distro = None

    if buildArkoudaImage(file):
        if tag:
            distro = getDistro(tag)
        else:
            if args.arkouda_branch:
                distro = args.arkouda_branch
            else:
                raise ValueError('Either --arkouda_tag or --arkouda_branch must be specified')
    
    buildImage(dockerRepo=dockerRepo,chapelVersion=chapelVersion,file=file,tag=tag,distro=distro)
