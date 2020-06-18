import ipaddress

import docker
from flask_redis import FlaskRedis
from redis.exceptions import LockError

from .db import DBContainer, DBConfig


class RedisUtils(FlaskRedis):
    def __init__(self, user_id=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key = 'ctfd_whale_lock-' + str(user_id)
        self.current_lock = None
        self.global_port_key = "ctfd_whale-port-set"
        self.global_network_key = "ctfd_whale-network-set"

    def init_redis_port_sets(self):
        configs = DBConfig.get_all_configs()

        self.delete(self.global_port_key)
        self.delete(self.global_network_key)

        containers = DBContainer.get_all_container()
        used_port_list = []
        for container in containers:
            if container.port != 0:
                used_port_list.append(container.port)
        for port in range(int(configs.get("frp_direct_port_minimum", 29000)),
                          int(configs.get("frp_direct_port_maximum", 28000)) + 1):
            if port not in used_port_list:
                self.add_available_port(port)

        client = docker.DockerClient(base_url=configs.get("docker_api_url"))
        docker_subnet = configs.get("docker_subnet", "174.1.0.0/16")
        try:
            docker_subnet = unicode(docker_subnet)
        except:
            pass
        docker_subnet_new_prefix = int(configs.get("docker_subnet_new_prefix", "24"))

        exist_networks = []
        available_networks = []

        for network in client.networks.list(filters={'label': 'prefix'}):
            exist_networks.append(str(network.attrs['Labels']['prefix']))

        for network in list(ipaddress.ip_network(docker_subnet).subnets(new_prefix=docker_subnet_new_prefix)):
            if str(network) not in exist_networks:
                available_networks.append(str(network))

        self.sadd(self.global_network_key, *set(available_networks))

    def add_available_network_range(self, network_range):
        self.sadd(self.global_network_key, network_range.encode())

    def get_available_network_range(self):
        return self.spop(self.global_network_key).decode()

    def add_available_port(self, port):
        self.sadd(self.global_port_key, str(port))

    def get_available_port(self):
        return int(self.spop(self.global_port_key))

    def acquire_lock(self):
        lock = self.lock(name=self.key, timeout=10)

        if not lock.acquire(blocking=True, blocking_timeout=2.0):
            return False

        self.current_lock = lock
        return True

    def release_lock(self):
        if self.current_lock is None:
            return False

        try:
            self.current_lock.release()

            return True
        except LockError:
            return False
