from __future__ import division  # Use floating point for math calculations

import fcntl
import json
import random
import uuid
from datetime import datetime

from flask import Blueprint, render_template, request
from flask_apscheduler import APScheduler

from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.utils import user as current_user
from CTFd.utils.decorators import admins_only, authed_only
from .control_utils import ControlUtil
from .db_utils import DBUtils
from .lock_utils import LockUtils
from .frp_utils import FrpUtils
from .models import DynamicDockerChallenge, DynamicValueDockerChallenge


def load(app):
    # upgrade()
    app.db.create_all()
    CHALLENGE_CLASSES["dynamic_docker"] = DynamicValueDockerChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/ctfd-whale/assets/"
    )

    page_blueprint = Blueprint(
        "ctfd-whale",
        __name__,
        template_folder="templates",
        static_folder="assets",
        url_prefix="/plugins/ctfd-whale"
    )

    @page_blueprint.route('/admin/settings', methods=['GET'])
    @admins_only
    def admin_list_configs():
        configs = DBUtils.get_all_configs()
        return render_template('config.html', configs=configs)

    @page_blueprint.route('/admin/settings', methods=['PATCH'])
    @admins_only
    def admin_save_configs():
        req = request.get_json()
        DBUtils.save_all_configs(req.items())
        return json.dumps({'success': True})

    @page_blueprint.route("/admin/containers", methods=['GET'])
    @admins_only
    def admin_list_containers():
        configs = DBUtils.get_all_configs()
        page = abs(request.args.get("page", 1, type=int))
        results_per_page = 50
        page_start = results_per_page * (page - 1)
        page_end = results_per_page * (page - 1) + results_per_page

        count = DBUtils.get_all_alive_container_count()
        containers = DBUtils.get_all_alive_container_page(page_start, page_end)

        pages = int(count / results_per_page) + (count % results_per_page > 0)
        return render_template("containers.html", containers=containers, pages=pages, curr_page=page,
                               curr_page_start=page_start, configs=configs)

    @page_blueprint.route("/admin/containers", methods=['DELETE'])
    @admins_only
    def admin_delete_container():
        user_id = request.args.get('user_id')
        ControlUtil.remove_container(user_id)
        return json.dumps({'success': True})

    @page_blueprint.route("/admin/containers", methods=['PATCH'])
    @admins_only
    def admin_renew_container():
        user_id = request.args.get('user_id')
        challenge_id = request.args.get('challenge_id')
        DBUtils.renew_current_container(user_id=user_id, challenge_id=challenge_id)
        return json.dumps({'success': True})

    @page_blueprint.route('/container', methods=['POST'])
    @authed_only
    def add_container():
        user_id = current_user.get_current_user().id
        lock_util = LockUtils(app=app, user_id=user_id)

        if not lock_util.acquire():
            return json.dumps({'success': False, 'msg': 'Request Too Fast!'})

        if ControlUtil.frequency_limit():
            return json.dumps({'success': False, 'msg': 'Frequency limit, You should wait at least 1 min.'})

        ControlUtil.remove_container(user_id)
        challenge_id = request.args.get('challenge_id')
        ControlUtil.check_challenge(challenge_id, user_id)

        configs = DBUtils.get_all_configs()
        current_count = DBUtils.get_all_alive_container_count()
        if int(configs.get("docker_max_container_count")) <= int(current_count):
            return json.dumps({'success': False, 'msg': 'Max container count exceed.'})

        dynamic_docker_challenge = DynamicDockerChallenge.query \
            .filter(DynamicDockerChallenge.id == challenge_id) \
            .first_or_404()
        flag = "flag{" + str(uuid.uuid4()) + "}"
        if dynamic_docker_challenge.redirect_type == "http":
            ControlUtil.add_container(user_id=user_id, challenge_id=challenge_id, flag=flag)
        else:
            port = random.randint(int(configs.get("frp_direct_port_minimum")),
                                  int(configs.get("frp_direct_port_maximum")))
            while True:
                if DBUtils.get_container_by_port(port) is None:
                    break
                port = random.randint(int(configs.get("frp_direct_port_minimum")),
                                      int(configs.get("frp_direct_port_maximum")))
            ControlUtil.add_container(user_id=user_id, challenge_id=challenge_id, flag=flag, port=port)

        lock_util.release()
        return json.dumps({'success': True})

    @page_blueprint.route('/container', methods=['GET'])
    @authed_only
    def list_container():
        user_id = current_user.get_current_user().id
        challenge_id = request.args.get('challenge_id')
        ControlUtil.check_challenge(challenge_id, user_id)
        data = DBUtils.get_current_containers(user_id=user_id)
        configs = DBUtils.get_all_configs()
        domain = configs.get('frp_http_domain_suffix', "")
        if data is not None:
            if int(data.challenge_id) != int(challenge_id):
                return json.dumps({})
            dynamic_docker_challenge = DynamicDockerChallenge.query \
                .filter(DynamicDockerChallenge.id == data.challenge_id) \
                .first_or_404()
            if dynamic_docker_challenge.redirect_type == "http":
                if int(configs.get('frp_http_port', "80")) == 80:
                    return json.dumps({'success': True, 'type': 'http', 'domain': data.uuid + domain,
                                       'remaining_time': 3600 - (datetime.now() - data.start_time).seconds})
                else:
                    return json.dumps({'success': True, 'type': 'http',
                                       'domain': data.uuid + domain + ":" + configs.get('frp_http_port', "80"),
                                       'remaining_time': 3600 - (datetime.now() - data.start_time).seconds})
            else:
                return json.dumps({'success': True, 'type': 'redirect', 'ip': configs.get('frp_direct_ip_address', ""),
                                   'port': data.port,
                                   'remaining_time': 3600 - (datetime.now() - data.start_time).seconds})
        else:
            return json.dumps({'success': True})

    @page_blueprint.route('/container', methods=['DELETE'])
    @authed_only
    def remove_container():
        user_id = current_user.get_current_user().id
        lock_util = LockUtils(app=app, user_id=user_id)
        if not lock_util.acquire():
            return json.dumps({'success': False, 'msg': 'Request Too Fast!'})

        if ControlUtil.frequency_limit():
            return json.dumps({'success': False, 'msg': 'Frequency limit, You should wait at least 1 min.'})

        if ControlUtil.remove_container(user_id):
            lock_util.release()

            return json.dumps({'success': True})
        else:
            return json.dumps({'success': False, 'msg': 'Failed when destroy instance, please contact admin!'})

    @page_blueprint.route('/container', methods=['PATCH'])
    @authed_only
    def renew_container():
        user_id = current_user.get_current_user().id
        lock_util = LockUtils(app=app, user_id=user_id)
        if not lock_util.acquire():
            return json.dumps({'success': False, 'msg': 'Request Too Fast!'})

        if ControlUtil.frequency_limit():
            return json.dumps({'success': False, 'msg': 'Frequency limit, You should wait at least 1 min.'})

        configs = DBUtils.get_all_configs()
        challenge_id = request.args.get('challenge_id')
        ControlUtil.check_challenge(challenge_id, user_id)
        docker_max_renew_count = int(configs.get("docker_max_renew_count"))
        container = DBUtils.get_current_containers(user_id)
        if container is None:
            return json.dumps({'success': False, 'msg': 'Instance not found.'})
        if container.renew_count >= docker_max_renew_count:
            return json.dumps({'success': False, 'msg': 'Max renewal times exceed.'})
        DBUtils.renew_current_container(user_id=user_id, challenge_id=challenge_id)
        lock_util.release()
        return json.dumps({'success': True})

    def auto_clean_container():
        with app.app_context():
            results = DBUtils.get_all_expired_container()
            for r in results:
                ControlUtil.remove_container(r.user_id)

            FrpUtils.update_frp_redirect()

    app.register_blueprint(page_blueprint)

    try:
        lock_file = open("/tmp/sanic.lock", "w")
        lock_fd = lock_file.fileno()
        fcntl.lockf(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

        scheduler = APScheduler()
        scheduler.init_app(app)
        scheduler.start()
        scheduler.add_job(id='whale-auto-clean', func=auto_clean_container, trigger="interval", seconds=10)
        print("[CTFd Whale]Started successfully")
    except IOError:
        pass
