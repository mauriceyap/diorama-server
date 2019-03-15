from typing import List

import docker
from docker.errors import NotFound
from docker.models.networks import Network
from docker.types import IPAMConfig, IPAMPool

import dict_keys
import constants

NETWORK_DRIVER = 'bridge'

DOCKER_CLIENT = docker.from_env()
DOCKER_API_CLIENT = docker.APIClient()


def get_container_run_command(runtime):
    return constants.RUNTIME_DATA[runtime][dict_keys.RUNTIME_DATA_RUN_COMMAND]


def get_container_working_directory(runtime):
    return constants.RUNTIME_DATA[runtime][dict_keys.RUNTIME_DATA_WORKING_DIRECTORY]


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


def create_container_and_connect(program_name: str, name: str, runtime: str, run_args: List, ip_address: str,
                                 udp_ports: List, network_name: str):
    DOCKER_API_CLIENT.create_container(
        program_name,
        name=name,
        command=get_container_run_command(runtime) + run_args,
        detach=True,
        working_dir=get_container_working_directory(runtime),
        ports=[(p, 'udp') for p in udp_ports]
    )
    DOCKER_CLIENT.networks.get(network_name).connect(name, ipv4_address=ip_address)
