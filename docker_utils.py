import json
import random
import traceback
import uuid
from collections import OrderedDict
import docker
from .db_utils import DBUtils
from .models import DynamicDockerChallenge
from .redis_utils import RedisUtils


class DockerUtils:

    @staticmethod
    def add_new_docker_container(app, user_id, challenge_id, flag, uuid_code):
        configs = DBUtils.get_all_configs()

        dynamic_docker_challenge = DynamicDockerChallenge.query \
            .filter(DynamicDockerChallenge.id == challenge_id) \
            .first_or_404()

        dns = configs.get("docker_dns", "").split(",")
        nodes = configs.get("docker_swarm_nodes", "").split(",")
        win_nodes = []
        linux_nodes = []
        for node in nodes:
            if node.startswith("windows"):
                win_nodes.append(node)
            else:
                linux_nodes.append(node)

        client = docker.DockerClient(base_url=configs.get("docker_api_url"))
        if dynamic_docker_challenge.docker_image.startswith("{"):
            images = json.loads(dynamic_docker_challenge.docker_image, object_pairs_hook=OrderedDict)

            redis_util = RedisUtils(app)
            range_prefix = redis_util.get_available_network_range()

            ipam_pool = docker.types.IPAMPool(
                subnet=range_prefix
            )
            ipam_config = docker.types.IPAMConfig(driver='default', pool_configs=[ipam_pool])
            network_name = str(user_id) + '-' + uuid_code
            network = client.networks.create(network_name, internal=True, ipam=ipam_config, attachable=True,
                                             labels={'prefix': range_prefix}, driver="overlay", scope="swarm")

            dns = []
            containers = configs.get("docker_auto_connect_containers", "").split(",")
            for c in containers:
                if c.find("dns") != -1:
                    network.connect(c)
                    network.reload()
                    for name in network.attrs['Containers']:
                        if network.attrs['Containers'][name]['Name'] == c:
                            dns.append(network.attrs['Containers'][name]['IPv4Address'].split('/')[0])
                else:
                    network.connect(c)

            has_processed_main = False
            for name in images:
                if not has_processed_main:
                    image = images[name]
                    container_name = str(user_id) + '-' + uuid_code

                    node = DockerUtils.choose_node(image, win_nodes, linux_nodes)

                    client.services.create(image=image, name=container_name, networks=[
                        docker.types.NetworkAttachmentConfig(network_name, aliases=[name])],
                                           env={'FLAG': flag}, dns_config=docker.types.DNSConfig(nameservers=dns),
                                           resources=docker.types.Resources(
                                               mem_limit=DockerUtils.convert_readable_text(
                                                   dynamic_docker_challenge.memory_limit),
                                               cpu_limit=int(
                                                   dynamic_docker_challenge.cpu_limit * 1e9)),
                                           labels={str(user_id) + '-' + uuid_code: str(user_id) + '-' + uuid_code},
                                           hostname=name, constraints=['node.labels.name==' + node],
                                           endpoint_spec=docker.types.EndpointSpec(mode='dnsrr', ports={}))
                    has_processed_main = True
                    continue

                image = images[name]
                container_name = str(user_id) + '-' + str(uuid.uuid4())
                client.services.create(image=image, name=container_name, networks=[
                    docker.types.NetworkAttachmentConfig(network_name, aliases=[name])],
                                       env={'FLAG': flag}, dns_config=docker.types.DNSConfig(nameservers=dns),
                                       resources=docker.types.Resources(mem_limit=DockerUtils.convert_readable_text(
                                           dynamic_docker_challenge.memory_limit),
                                           cpu_limit=int(
                                               dynamic_docker_challenge.cpu_limit * 1e9)),
                                       labels={str(user_id) + '-' + uuid_code: str(user_id) + '-' + uuid_code},
                                       hostname=name, constraints=['node.labels.name==' + node],
                                       endpoint_spec=docker.types.EndpointSpec(mode='dnsrr', ports={}))

        else:
            node = DockerUtils.choose_node(dynamic_docker_challenge.docker_image, win_nodes, linux_nodes)

            client.services.create(image=dynamic_docker_challenge.docker_image, name=str(user_id) + '-' + uuid_code,
                                   env={'FLAG': flag}, dns_config=docker.types.DNSConfig(nameservers=dns),
                                   networks=[configs.get("docker_auto_connect_network", "ctfd_frp-containers")],
                                   resources=docker.types.Resources(mem_limit=DockerUtils.convert_readable_text(
                                       dynamic_docker_challenge.memory_limit),
                                       cpu_limit=int(
                                           dynamic_docker_challenge.cpu_limit * 1e9)),
                                   constraints=['node.labels.name==' + node],
                                   endpoint_spec=docker.types.EndpointSpec(mode='dnsrr', ports={}))

    @staticmethod
    def choose_node(image, win_nodes, linux_nodes):
        is_win = False
        image_split = image.split(":")
        if len(image_split) > 1:
            if image_split[1].startswith("windows"):
                is_win = True

        if is_win:
            node = random.choice(win_nodes)
        else:
            node = random.choice(linux_nodes)

        return node

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
    def remove_current_docker_container(app, user_id, is_retry=False):
        configs = DBUtils.get_all_configs()
        container = DBUtils.get_current_containers(user_id=user_id)

        auto_containers = configs.get("docker_auto_connect_containers", "").split(",")

        if container is None:
            return False

        try:
            client = docker.DockerClient(base_url=configs.get("docker_api_url"))
            networks = client.networks.list(names=[str(user_id) + '-' + container.uuid])

            if len(networks) == 0:
                services = client.services.list(filters={'name': str(user_id) + '-' + container.uuid})
                for s in services:
                    s.remove()
            else:
                redis_util = RedisUtils(app)
                services = client.services.list(filters={'label': str(user_id) + '-' + container.uuid})
                for s in services:
                    s.remove()

                for n in networks:
                    for ac in auto_containers:
                        try:
                            n.disconnect(ac, force=True)
                        except:
                            pass
                    n.remove()
                    redis_util.add_available_network_range(n.attrs['Labels']['prefix'])
        except:
            traceback.print_exc()
            if not is_retry:
                DockerUtils.remove_current_docker_container(app, user_id, True)

        return True
