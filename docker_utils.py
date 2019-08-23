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

        client = docker.DockerClient(base_url=configs.get("docker_api_url"))
        client.containers.run(image=dynamic_docker_challenge.docker_image, name=str(user_id) + '-' + uuid_code,
                              environment={'FLAG': flag}, detach=True, network="ctfd_frp-containers",
                              mem_limit=dynamic_docker_challenge.memory_limit)

    @staticmethod
    def remove_current_docker_container(user_id, is_retry = False):
        configs = DBUtils.get_all_configs()
        container = DBUtils.get_current_containers(user_id=user_id)

        if container is None:
            return

        try:
            client = docker.DockerClient(base_url=configs.get("docker_api_url"))
            containers = client.containers.list(filters={'name': str(user_id) + '-' + container.uuid})
            for c in containers:
                c.remove(force=True)
        except:
            if not is_retry:
                DockerUtils.remove_current_docker_container(user_id, True)
