from typing import List

import docker
from docker.errors import NotFound
from docker.models.networks import Network
from docker.types import IPAMConfig, IPAMPool

NETWORK_DRIVER = 'bridge'

DOCKER_CLIENT = docker.from_env()
DOCKER_API_CLIENT = docker.APIClient()


def remove_network(network_id: str):
    try:
        existing_network: Network = DOCKER_CLIENT.networks.get(network_id)
        existing_network.remove()
    except NotFound:
        pass


def remove_containers(container_ids: List[str]):
    for container_id in container_ids:
        try:
            DOCKER_CLIENT.containers.get(container_id).remove(force=True)
        except NotFound:
            pass


def remove_images(image_names: List[str]):
    for image_name in image_names:
        try:
            DOCKER_CLIENT.images.remove(image=image_name, force=True, noprune=False)
        except NotFound:
            pass


def create_image(path, tag: str):
    DOCKER_CLIENT.images.build(path=path, tag=tag, rm=True)


def create_network(network_name: str, network_subnet):
    DOCKER_CLIENT.networks.create(
        name=network_name,
        driver=NETWORK_DRIVER,
        ipam=IPAMConfig(pool_configs=[IPAMPool(subnet=network_subnet)]),
        internal=True
    )
