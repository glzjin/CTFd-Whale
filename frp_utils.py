import requests

from .db_utils import DBUtils
from .models import DynamicDockerChallenge


class FrpUtils:
    @staticmethod
    def update_frp_redirect():
        configs = DBUtils.get_all_configs()
        domain = configs.get('frp_http_domain_suffix', "")

        containers = DBUtils.get_all_alive_container()

        output = configs.get("frp_config_template")

        http_template = "\n\n[http_%s]\n" + \
                        "type = http\n" + \
                        "local_ip = %s\n" + \
                        "local_port = %s\n" + \
                        "custom_domains = %s\n" + \
                        "use_compression = true"

        direct_template = "\n\n[direct_%s]\n" + \
                          "type = tcp\n" + \
                          "local_ip = %s\n" + \
                          "local_port = %s\n" + \
                          "remote_port = %s\n" + \
                          "use_compression = true" + \
                          "\n\n[direct_%s_udp]\n" + \
                          "type = udp\n" + \
                          "local_ip = %s\n" + \
                          "local_port = %s\n" + \
                          "remote_port = %s\n" + \
                          "use_compression = true"

        for c in containers:
            dynamic_docker_challenge = DynamicDockerChallenge.query \
                .filter(DynamicDockerChallenge.id == c.challenge_id) \
                .first_or_404()

            if dynamic_docker_challenge.redirect_type == 'http':
                output += http_template % (
                    str(c.user_id) + '-' + c.uuid, str(c.user_id) + '-' + c.uuid,
                    dynamic_docker_challenge.redirect_port, c.uuid + domain)
            else:
                output += direct_template % (
                    str(c.user_id) + '-' + c.uuid, str(c.user_id) + '-' + c.uuid,
                    dynamic_docker_challenge.redirect_port, c.port,
                    str(c.user_id) + '-' + c.uuid, str(c.user_id) + '-' + c.uuid,
                    dynamic_docker_challenge.redirect_port, c.port)

        requests.put("http://" + configs.get("frp_api_ip") + ":" + configs.get("frp_api_port") + "/api/config", output,
                     timeout=5)
        requests.get("http://" + configs.get("frp_api_ip") + ":" + configs.get("frp_api_port") + "/api/reload", timeout=5)
