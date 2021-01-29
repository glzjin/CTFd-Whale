from datetime import datetime
from flask import request, abort
from flask_restx import Namespace, Resource
from werkzeug.exceptions import Forbidden, NotFound

from CTFd.utils import user as current_user
from CTFd.utils import get_config, set_config
from CTFd.utils.decorators import admins_only, authed_only
from .decorators import challenge_visible, frequency_limited
from .utils.control import ControlUtil
from .utils.db import DBContainer

admin_namespace = Namespace("ctfd-whale-admin")
user_namespace = Namespace("ctfd-whale-user")


@admin_namespace.errorhandler(NotFound)
@user_namespace.errorhandler(NotFound)
def handle_notfound(err):
    data = {
        'success': False,
        'message': err.description
    }
    return data, 404


@admin_namespace.errorhandler(Forbidden)
@user_namespace.errorhandler(Forbidden)
def handle_forbidden(err):
    if 'You don\'t have the permission' not in err.description:
        message = err.description
    else:
        message = 'Please login first'
    data = {
        'success': False,
        'message': message
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


@admin_namespace.route('/container')
class AdminContainers(Resource):
    @staticmethod
    @admins_only
    def get():
        page = abs(request.args.get("page", 1, type=int))
        results_per_page = abs(request.args.get("per_page", 20, type=int))
        page_start = results_per_page * (page - 1)
        page_end = results_per_page * (page - 1) + results_per_page

        count = DBContainer.get_all_alive_container_count()
        containers = DBContainer.get_all_alive_container_page(
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
        user_id = request.args.get('user_id', -1)
        result, message = ControlUtil.try_renew_container(user_id=int(user_id))
        if not result:
            abort(403, message)
        return {'success': True, 'message': message}

    @staticmethod
    @admins_only
    def delete():
        user_id = request.args.get('user_id')
        result, message = ControlUtil.try_remove_container(user_id)
        return {'success': result, 'message': message}


@user_namespace.route("/container")
class UserContainers(Resource):
    @staticmethod
    @authed_only
    @challenge_visible
    def get():
        user_id = current_user.get_current_user().id
        challenge_id = request.args.get('challenge_id')
        container = DBContainer.get_current_containers(user_id=user_id)
        if not container:
            return {'success': True, 'data': {}}
        timeout = int(get_config("whale:docker_timeout", "3600"))
        if int(container.challenge_id) != int(challenge_id):
            return {
                'success': False,
                'message': f'Container started but not from this challenge ({container.challenge_id})'
            }
        return {
            'success': True,
            'data': {
                'lan_domain': str(user_id) + "-" + container.uuid,
                'user_access': container.user_access,
                'remaining_time': timeout - (datetime.now() - container.start_time).seconds,
            }
        }

    @staticmethod
    @authed_only
    @challenge_visible
    @frequency_limited
    def post():
        user_id = current_user.get_current_user().id
        ControlUtil.try_remove_container(user_id)

        current_count = DBContainer.get_all_alive_container_count()
        if int(get_config("whale:docker_max_container_count")) <= int(current_count):
            abort(403, 'Max container count exceed.')

        challenge_id = request.args.get('challenge_id')
        result, message = ControlUtil.try_add_container(
            user_id=user_id,
            challenge_id=challenge_id
        )
        if not result:
            abort(403, message)
        return {'success': True, 'message': message}

    @staticmethod
    @authed_only
    @challenge_visible
    @frequency_limited
    def patch():
        user_id = current_user.get_current_user().id
        docker_max_renew_count = int(get_config("whale:docker_max_renew_count", 5))
        container = DBContainer.get_current_containers(user_id)
        if container is None:
            abort(403, 'Instance not found.')
        if container.renew_count >= docker_max_renew_count:
            abort(403, 'Max renewal count exceed.')
        result, message = ControlUtil.try_renew_container(user_id=user_id)
        return {'success': result, 'message': message}

    @staticmethod
    @authed_only
    @frequency_limited
    def delete():
        user_id = current_user.get_current_user().id
        result, message = ControlUtil.try_remove_container(user_id)
        if not result:
            abort(403, message)
        return {'success': True, 'message': message}
