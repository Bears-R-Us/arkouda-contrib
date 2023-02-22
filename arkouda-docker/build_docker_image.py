import argparse, enum, subprocess, sys
from typing import Optional
from enum import Enum

class ImageType(Enum):
    '''
    The ImageType enum provides controlled vocabulary for the docker image type
    '''
    ARKOUDA_FULL_STACK = 'ARKOUDA_FULL_STACK'
    ARKOUDA_SMP_SERVER = 'ARKOUDA_SMP_SERVER'
    ARKOUDA_UDP_SERVER = 'ARKOUDA_UDP_SERVER'
    CHAPEL_UDP = 'CHAPEL_UDP'

def getImageFile(imageType: ImageType) -> str:
    '''
    Returns the Dockerfile per the image type

    
    :return: Dockerfile corresponding to the image type
    :rtype: str
    '''
    if ImageType.ARKOUDA_FULL_STACK == imageType:
        return 'arkouda-full-stack'
    elif ImageType.ARKOUDA_SMP_SERVER == imageType:
        return 'arkouda-smp-server'
    elif ImageType.ARKOUDA_UDP_SERVER == imageType:
        return 'arkouda-udp-server'
    elif ImageType.CHAPEL_UDP == imageType:
        return 'chapel-gasnet-udp'

def getDistro(tag: str) -> str:
    '''
    Returns the distro name corresponding to the Arkouda tag

    :param str tag: Arkouda tag
    :return: distro name 
    :rtype: str
    '''
    return tag.lstrip('v')

def buildImage(repo: str, chapelVersion: str, file: str, distro: str, tag: Optional[str]) -> None:
    '''
    Generates a build tag and then builds the desired docker image

    :param str repo: dockerhub repo the image will be published to
    :param str chapelVersion: version of Chapel used to build Arkouda server
    :param str file: Dockerfile name
    :param str distro: Arkouda distro (branch name)
    :param Optional[str] tag: Arkouda tag name, if applicable
    :return: None
    '''
    buildTag = generateBuildTag(repo=repo, file=file, tag=tag,distro=distro)
    print(buildTag)
    #p = subprocess.Popen(shell=True, args=['docker','build','-f',image,chapelVersion])

def generateBuildTag(repo: str, file: str, tag: Optional[str], distro: Optional[str]) -> str:
    '''
    Generates a docker build tag corresponding to the repo, file, tag, an distro

    :param str repo: dockerhub repo the image will be published to
    :param str file: Dockerfile name
    :param Optional[str] tag: Arkouda tag name, if applicable
    :param Optional[str] distro: Arkouda distro (branch name), if applicable

    :return: docker build tag 
    :rtype: str
    '''
    if tag:
        return f'{repo}/{file}:{tag}'
    else:
        return f'{repo}/{file}:{distro}'   

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Build bearsrus docker images')

    parser.add_argument('--image_type', type=ImageType,
                        help='possible image types are ARKOUDA_FULL_STACK, ARKOUDA_SMP_SERVER, ARKOUDA_UDP_SERVER and CHAPEL_UDP')
    parser.add_argument('--arkouda_tag', type=str,
                        help='if the desired arkouda version is a tag')
    parser.add_argument('--arkouda_branch', type=str, 
                        help='if the desired arkouda version is a branch')
    parser.add_argument('--dockerhub_repo', type=str, default='Bears-R-Us',
                        help='the dockerhub repo the image is to be published, defaults to Bears-R-Us')
    parser.add_argument('--chapel_version', type=str,
                        help='Version of Chapel used to build image')

    args = parser.parse_args()

    file = getImageFile(args.image_type)
    tag = args.arkouda_tag
    repo = args.dockerhub_repo
    chapelVersion = args.chapel_version

    if tag:
        distro = getDistro(tag)
    else:
        if args.arkouda_branch:
            distro = args.arkouda_branch
        else:
            raise ValueError('Either --arkouda_tag or --arkouda_branch must be specified')
    
    buildImage(repo=repo,chapelVersion=chapelVersion,file=file,tag=tag,distro=distro)
