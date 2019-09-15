import json
import random
import uuid
from collections import OrderedDict

import docker
from .db_utils import DBUtils
from .models import DynamicDockerChallenge


class DockerUtils:
    @staticmethod
    def add_new_docker_container(user_id, challenge_id, flag, uuid_code):
        configs = DBUtils.get_all_configs()

        dynamic_docker_challenge = DynamicDockerChallenge.query \
            .filter(DynamicDockerChallenge.id == challenge_id) \
            .first_or_404()

        dns = configs.get("docker_dns", "").split(",")

        client = docker.DockerClient(base_url=configs.get("docker_api_url"))
        if dynamic_docker_challenge.docker_image.startswith("{"):
            images = json.loads(dynamic_docker_challenge.docker_image, object_pairs_hook=OrderedDict)

            range_prefix = '172.64.' + str(random.randint(10, 200))
            while True:
                if len(client.networks.list(filters={'label': range_prefix})) == 0:
                    break
                range_prefix = '172.64.' + str(random.randint(10, 200))

            ipam_pool = docker.types.IPAMPool(
                subnet=range_prefix + '.0/24',
                gateway=range_prefix + '.254'
            )
            ipam_config = docker.types.IPAMConfig(driver='default', pool_configs=[ipam_pool])
            network_name = str(user_id) + '-' + uuid_code
            network = client.networks.create(network_name, internal=True, ipam=ipam_config,
                                             labels={range_prefix: range_prefix})

            dns = []
            end_ip = 250
            containers = configs.get("docker_auto_connect_containers", "").split(",")
            for c in containers:
                if c.find("dns") != -1:
                    network.connect(c, ipv4_address=range_prefix + "." + str(end_ip))
                    dns.append(range_prefix + "." + str(end_ip))
                    end_ip += 1
                else:
                    network.connect(c)

            has_processed_main = False
            for name in images:
                if not has_processed_main:
                    image = images[name]
                    container_name = str(user_id) + '-' + uuid_code
                    client.containers.run(image=image, name=container_name, network=network_name,
                                          environment={'FLAG': flag}, detach=True, dns=dns,
                                          mem_limit=dynamic_docker_challenge.memory_limit,
                                          nano_cpus=int(dynamic_docker_challenge.cpu_limit * 1e9),
                                          labels={str(user_id) + '-' + uuid_code: str(user_id) + '-' + uuid_code},
                                          hostname=name, auto_remove=True, pids_limit=200)
                    network.disconnect(container_name)
                    network.connect(container_name, aliases=[name])
                    has_processed_main = True
                    continue

                image = images[name]
                container_name = str(user_id) + '-' + str(uuid.uuid4())
                client.containers.run(image=image, name=container_name, network=network_name,
                                      environment={'FLAG': flag}, detach=True, dns=dns,
                                      mem_limit=dynamic_docker_challenge.memory_limit,
                                      nano_cpus=int(dynamic_docker_challenge.cpu_limit * 1e9),
                                      labels={str(user_id) + '-' + uuid_code: str(user_id) + '-' + uuid_code},
                                      hostname=name, auto_remove=True, pids_limit=200)
                network.disconnect(container_name)
                network.connect(container_name, aliases=[name])

        else:
            client.containers.run(image=dynamic_docker_challenge.docker_image, name=str(user_id) + '-' + uuid_code,
                                  environment={'FLAG': flag}, detach=True, dns=dns,
                                  network=configs.get("docker_auto_connect_network", "ctfd_frp-containers"),
                                  mem_limit=dynamic_docker_challenge.memory_limit,
                                  nano_cpus=int(dynamic_docker_challenge.cpu_limit * 1e9), auto_remove=True,
                                  pids_limit=200)

    @staticmethod
    def remove_current_docker_container(user_id, is_retry=False):
        configs = DBUtils.get_all_configs()
        container = DBUtils.get_current_containers(user_id=user_id)

        auto_containers = configs.get("docker_auto_connect_containers", "").split(",")

        if container is None:
            return False

        try:
            client = docker.DockerClient(base_url=configs.get("docker_api_url"))
            networks = client.networks.list(names=[str(user_id) + '-' + container.uuid])

            if len(networks) == 0:
                containers = client.containers.list(filters={'name': str(user_id) + '-' + container.uuid})
                for c in containers:
                    c.remove(v=True, force=True)
            else:
                containers = client.containers.list(filters={'label': str(user_id) + '-' + container.uuid})
                for c in containers:
                    c.remove(v=True, force=True)

                for n in networks:
                    for ac in auto_containers:
                        n.disconnect(ac)
                    n.remove()
        except:
            if not is_retry:
                DockerUtils.remove_current_docker_container(user_id, True)

        return True
