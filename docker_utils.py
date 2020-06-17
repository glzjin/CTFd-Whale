import json
import random
import uuid
from collections import OrderedDict

import docker
from flask import current_app

from .db_utils import DBUtils
from .redis_utils import RedisUtils
from .utils import WhaleError


class DockerUtils:
    @staticmethod
    def add_container(container):
        configs = DBUtils.get_all_configs()
        try:
            client = docker.DockerClient(base_url=configs["docker_api_url"])
        except Exception as e:
            raise WhaleError(
                'Docker Connection Error' +
                'Please ensure the docker api url (first config item) is correct' +
                'if you are using unix:///var/run/docker.sock, check if the socket is correctly mapped'
            )
        if container.challenge.docker_image.startswith("{"):
            DockerUtils._create_grouped_container(client, container, configs)
        else:
            DockerUtils._create_standalone_container(client, container, configs)

    @staticmethod
    def _create_standalone_container(client, container, configs):
        print(RedisUtils(app=current_app).get_available_network_range())
        dns = configs.get("docker_dns", "").split(",")
        node = DockerUtils.choose_node(
            container.challenge.docker_image,
            configs.get("docker_swarm_nodes", "").split(",")
        )

        client.services.create(
            image=container.challenge.docker_image,
            name=f'{container.user_id}-{container.uuid}',
            env={'FLAG': container.flag}, dns_config=docker.types.DNSConfig(nameservers=dns),
            networks=[configs.get("docker_auto_connect_network", "ctfd_frp-containers")],
            resources=docker.types.Resources(
                mem_limit=DockerUtils.convert_readable_text(
                    container.challenge.memory_limit),
                cpu_limit=int(container.challenge.cpu_limit * 1e9)
            ),
            labels={
                'whale_id': f'{container.user_id}-{container.uuid}'
            },  # for container deletion
            constraints=['node.labels.name==' + node],
            endpoint_spec=docker.types.EndpointSpec(mode='dnsrr', ports={})
        )

    @staticmethod
    def _create_grouped_container(client, container, configs):
        range_prefix = RedisUtils(app=current_app).get_available_network_range()

        ipam_pool = docker.types.IPAMPool(subnet=range_prefix)
        ipam_config = docker.types.IPAMConfig(
            driver='default', pool_configs=[ipam_pool])
        network_name = f'{container.user_id}-{container.uuid}'
        network = client.networks.create(
            network_name, internal=True,
            ipam=ipam_config, attachable=True,
            labels={'prefix': range_prefix},
            driver="overlay", scope="swarm"
        )

        dns = []
        containers = configs.get("docker_auto_connect_containers", "").split(",")
        for c in containers:
            network.connect(c)
            if "dns" in c:
                network.reload()
                for name in network.attrs['Containers']:
                    if network.attrs['Containers'][name]['Name'] == c:
                        dns.append(network.attrs['Containers'][name]['IPv4Address'].split('/')[0])

        has_processed_main = False

        images = json.loads(
            container.challenge.docker_image,
            object_pairs_hook=OrderedDict
        )
        for name, image in images.items():
            if not has_processed_main:
                container_name = f'{container.user_id}-{container.uuid}'
            else:
                container_name = f'{container.user_id}-{uuid.uuid4()}'
                node = DockerUtils.choose_node(image, configs.get("docker_swarm_nodes", "").split(","))
                has_processed_main = True
            client.services.create(
                image=image, name=container_name, networks=[
                    docker.types.NetworkAttachmentConfig(network_name, aliases=[name])
                ],
                env={'FLAG': container.flag},
                dns_config=docker.types.DNSConfig(nameservers=dns),
                resources=docker.types.Resources(
                    mem_limit=DockerUtils.convert_readable_text(
                        container.challenge.memory_limit
                    ),
                    cpu_limit=int(container.challenge.cpu_limit * 1e9)),
                labels={
                    'whale_id': f'{container.user_id}-{container.uuid}'
                },  # for container deletion
                hostname=name, constraints=['node.labels.name==' + node],
                endpoint_spec=docker.types.EndpointSpec(mode='dnsrr', ports={})
            )

    @staticmethod
    def remove_container(container):
        configs = DBUtils.get_all_configs()

        whale_id = f'{container.user_id}-{container.uuid}'

        try:
            client = docker.DockerClient(base_url=configs.get("docker_api_url"))
        except Exception as e:
            raise WhaleError(
                'Docker Connection Error' +
                'Please ensure the docker api url (first config item) is correct' +
                'if you are using unix:///var/run/docker.sock, check if the socket is correctly mapped'
            )
        for s in client.services.list(filters={'label': f'whale_id={whale_id}'}):
            s.remove()

        networks = client.networks.list(names=[whale_id])
        if len(networks) > 0:  # is grouped containers
            auto_containers = configs.get("docker_auto_connect_containers", "").split(",")
            redis_util = RedisUtils(current_app)
            for network in networks:
                for container in auto_containers:
                    try:
                        network.disconnect(container, force=True)
                    except:
                        pass
                redis_util.add_available_network_range(network.attrs['Labels']['prefix'])
                network.remove()

    @staticmethod
    def convert_readable_text(text):
        lower_text = text.lower()

        if lower_text.endswith("k"):
            return int(text[:-1]) * 1024

        if lower_text.endswith("m"):
            return int(text[:-1]) * 1024 * 1024

        if lower_text.endswith("g"):
            return int(text[:-1]) * 1024 * 1024 * 1024

        return 0

    @staticmethod
    def choose_node(image, nodes):
        win_nodes = []
        linux_nodes = []
        for node in nodes:
            if node.startswith("windows"):
                win_nodes.append(node)
            else:
                linux_nodes.append(node)
        try:
            tag = image.split(":")[1:]
            if len(tag) and tag[0].startswith("windows"):
                return random.choice(win_nodes)
            return random.choice(linux_nodes)
        except IndexError:
            raise WhaleError(
                'No Suitable Nodes.\n' +
                'If you are using Whale for the first time, \n' +
                'Please Setup Swarm Nodes Correctly and Lable Them with\n' +
                'docker node update --label-add "name=linux-1" $(docker node ls -q)'
            )
