from __future__ import division  # Use floating point for math calculations

import fcntl

import requests
from flask import Blueprint, render_template
from flask_apscheduler import APScheduler

from CTFd.api import CTFd_API_v1
from CTFd.plugins import (
    register_plugin_assets_directory,
    register_admin_plugin_menu_bar,
)
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from .api import *
from .challenge_type import DynamicValueDockerChallenge
from .control_utils import ControlUtil
from .db_utils import DBUtils
from .redis_utils import RedisUtils


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
    register_admin_plugin_menu_bar(
        'Whale', '/plugins/ctfd-whale/admin/settings'
    )
    CTFd_API_v1.add_namespace(admin_namespace, path="/plugins/ctfd-whale/admin")
    CTFd_API_v1.add_namespace(user_namespace, path="/plugins/ctfd-whale")

    @page_blueprint.route('/admin/settings', methods=['GET'])
    @admins_only
    def admin_list_configs():
        configs = DBUtils.get_all_configs()
        return render_template('config/config.html', configs=configs)

    @page_blueprint.route("/admin/containers")
    @admins_only
    def admin_list_containers():
        result = AdminContainers.get()
        return render_template("containers.html",
                               containers=result['data']['containers'],
                               pages=result['data']['pages'],
                               curr_page=abs(request.args.get("page", 1, type=int)),
                               curr_page_start=result['data']['page_start'])

    def auto_clean_container():
        with app.app_context():
            results = DBUtils.get_all_expired_container()
            for r in results:
                ControlUtil.try_remove_container(r.user_id)

            configs = DBUtils.get_all_configs()
            containers = DBUtils.get_all_alive_container()

            output = configs.get("frp_config_template")

            for c in containers:
                output += c.frp_config

            requests.put(f'http://{configs.get("frp_api_ip")}:{configs.get("frp_api_port")}/api/config',
                         output, timeout=5)
            requests.get(f'http://{configs.get("frp_api_ip")}:{configs.get("frp_api_port")}/api/reload',
                         timeout=5)

    app.register_blueprint(page_blueprint)

    try:
        lock_file = open("/tmp/ctfd_whale.lock", "w")
        lock_fd = lock_file.fileno()
        fcntl.lockf(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

        scheduler = APScheduler()
        scheduler.init_app(app)
        scheduler.start()
        scheduler.add_job(id='whale-auto-clean', func=auto_clean_container, trigger="interval", seconds=10)

        redis_util = RedisUtils(app=app)
        redis_util.init_redis_port_sets()

        print("[CTFd Whale]Started successfully")
    except IOError:
        pass
