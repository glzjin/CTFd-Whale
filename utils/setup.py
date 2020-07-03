from .db import DBConfig


def setup_default_configs():
    DBConfig.set_all_configs({
        'setup': 'true',
        'docker_api_url': 'unix:///var/run/docker.sock',
        'docker_dns': '127.0.0.1',
        'docker_max_container_count': '100',
        'docker_max_renew_count': '5',
        'docker_subnet': '174.1.0.0/16',
        'docker_subnet_new_prefix': '24',
        'docker_swarm_nodes': 'linux-1',
        'docker_timeout': '3600',
        'frp_api_url': 'http://frpc:7400',
        'frp_direct_port_maximum': '10100',
        'frp_direct_port_minimum': '10000',
        'template_http_subdomain': '{{ container.uuid }}',
        'template_chall_flag': '{{ "flag{"+uuid.uuid4()|string+"}" }}',
    })
