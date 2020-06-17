from datetime import datetime

from flask import request, current_app
from flask_restx import Namespace, Resource
from werkzeug.exceptions import Forbidden

from CTFd.utils import user as current_user
from CTFd.utils.decorators import admins_only, authed_only
from .control_utils import ControlUtil
from .db_utils import DBUtils
from .redis_utils import RedisUtils

admin_namespace = Namespace("ctfd-whale-admin")
user_namespace = Namespace("ctfd-whale-user")


@admin_namespace.errorhandler(Forbidden)
@user_namespace.errorhandler(Forbidden)
def handle_forbidden(err):
    data = {
        'success': False,
        'message': 'Please login first'
    }
    return data, 403


@admin_namespace.errorhandler
@user_namespace.errorhandler
def handle_default(err):
    data = {
        'success': False,
        'message': 'Unexpected things happened'
    }
    return data, 500


@admin_namespace.route('/settings')
class AdminSettings(Resource):
    @admins_only
    def patch(self):
        req = request.get_json()
        DBUtils.save_all_configs(req.items())
        redis_util = RedisUtils(app=current_app)
        redis_util.init_redis_port_sets()
        return {'success': True}


@admin_namespace.route('/container')
class AdminContainers(Resource):
    @staticmethod
    @admins_only
    def get():
        page = abs(request.args.get("page", 1, type=int))
        results_per_page = abs(request.args.get("per_page", 50, type=int))
        page_start = results_per_page * (page - 1)
        page_end = results_per_page * (page - 1) + results_per_page

        count = DBUtils.get_all_alive_container_count()
        containers = DBUtils.get_all_alive_container_page(
            page_start, page_end)

        return {'success': True, 'data': {
            'containers': containers,
            'total': count,
            'pages': int(count / results_per_page) + (count % results_per_page > 0),
            'page_start': page_start,
        }}

    @staticmethod
    @admins_only
    def patch():
        user_id = request.args.get('user_id')
        challenge_id = request.args.get('challenge_id')
        DBUtils.renew_current_container(
            user_id=user_id, challenge_id=challenge_id)
        return {'success': True}

    @staticmethod
    @admins_only
    def delete():
        user_id = request.args.get('user_id')
        return {'success': ControlUtil.try_remove_container(user_id)}


@user_namespace.route("/container")
class UserContainers(Resource):
    @staticmethod
    @authed_only
    def get():
        user_id = current_user.get_current_user().id
        challenge_id = request.args.get('challenge_id')
        ControlUtil.check_challenge(challenge_id)
        data = DBUtils.get_current_containers(user_id=user_id)
        timeout = int(DBUtils.get_config("docker_timeout", "3600"))
        if data is not None:
            if int(data.challenge_id) != int(challenge_id):
                return {
                    'success': False,
                    'message': f'Container started but not from this challenge ({data.challenge_id})'
                }
            return {
                'success': True,
                'data': {
                    'lan_domain': str(user_id) + "-" + data.uuid,
                    'type': 'http',
                    'user_access': data.user_access,
                    'remaining_time': timeout - (datetime.now() - data.start_time).seconds,
                }
            }
        else:
            return {'success': True, 'data': {}}

    @staticmethod
    @authed_only
    def post():
        user_id = current_user.get_current_user().id
        redis_util = RedisUtils(app=current_app, user_id=user_id)

        if not redis_util.acquire_lock():
            return {'success': False, 'message': 'Request Too Fast!'}

        if ControlUtil.frequency_limit():
            return {'success': False, 'message': 'Frequency limit, You should wait at least 1 min.'}

        ControlUtil.try_remove_container(user_id)
        challenge_id = request.args.get('challenge_id')
        ControlUtil.check_challenge(challenge_id)

        current_count = DBUtils.get_all_alive_container_count()
        if int(DBUtils.get_config("docker_max_container_count")) <= int(current_count):
            return {'success': False, 'message': 'Max container count exceed.'}

        if not ControlUtil.try_add_container(
                user_id=user_id,
                challenge_id=challenge_id):
            return {'success': False, 'message': 'No available ports. Please wait for a few minutes.'}
        redis_util.release_lock()
        return {'success': True}

    @staticmethod
    @authed_only
    def patch():
        user_id = current_user.get_current_user().id
        redis_util = RedisUtils(app=current_app, user_id=user_id)
        if not redis_util.acquire_lock():
            return {'success': False, 'message': 'Request Too Fast!'}

        if ControlUtil.frequency_limit():
            return {'success': False, 'message': 'Frequency limit, You should wait at least 1 min.'}

        challenge_id = request.args.get('challenge_id')
        ControlUtil.check_challenge(challenge_id)
        docker_max_renew_count = int(DBUtils.get_config("docker_max_renew_count"))
        container = DBUtils.get_current_containers(user_id)
        if container is None:
            return {'success': False, 'message': 'Instance not found.'}
        if container.renew_count >= docker_max_renew_count:
            return {'success': False, 'message': 'Max renewal times exceed.'}
        DBUtils.renew_current_container(user_id=user_id, challenge_id=challenge_id)
        redis_util.release_lock()
        return {'success': True}

    @staticmethod
    @authed_only
    def delete():
        user_id = current_user.get_current_user().id
        redis_util = RedisUtils(app=current_app, user_id=user_id)
        if not redis_util.acquire_lock():
            return {'success': False, 'message': 'Request Too Fast!'}

        if ControlUtil.frequency_limit():
            return {'success': False, 'message': 'Frequency limit, You should wait at least 1 min.'}

        if ControlUtil.try_remove_container(user_id):
            redis_util.release_lock()

            return {'success': True}
        else:
            return {'success': False, 'message': 'Failed when destroy instance, please contact admin!'}
