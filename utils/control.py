import datetime
import traceback
from flask import current_app

from CTFd.utils import get_config
from .cache import CacheProvider
from .db import DBContainer, db
from .docker import DockerUtils


class ControlUtil:
    @staticmethod
    def try_add_container(user_id, challenge_id):
        port = CacheProvider(app=current_app).get_available_port()
        if not port:
            return False, 'No available ports. Please wait for a few minutes.'
        container = DBContainer.create_container_record(user_id, challenge_id, port)
        DockerUtils.add_container(container)
        return True, 'Container created'

    @staticmethod
    def try_remove_container(user_id):
        container = DBContainer.get_current_containers(user_id=user_id)
        if not container:
            return False, 'No such container'
        for _ in range(3):  # configurable? as "onerror_retry_cnt"
            try:
                DockerUtils.remove_container(container)
                if container.port != 0:
                    redis_util = CacheProvider(app=current_app)
                    redis_util.add_available_port(container.port)
                DBContainer.remove_container_record(user_id)
                return True, 'Container destroyed'
            except:
                traceback.print_exc()
        return False, 'Failed when destroying instance, please contact admin!'

    @staticmethod
    def try_renew_container(user_id):
        container = DBContainer.get_current_containers(user_id)
        if not container:
            return False, 'No such container'
        timeout = int(get_config("whale:docker_timeout", "3600"))
        container.start_time = container.start_time + \
                               datetime.timedelta(seconds=timeout)
        if container.start_time > datetime.datetime.now():
            container.start_time = datetime.datetime.now()
            # race condition? useless maybe?
            # useful when docker_timeout < poll timeout (10 seconds)
            # doesn't make any sense
        else:
            return False, 'Invalid container'
        container.renew_count += 1
        db.session.commit()
        return True, 'Container Renewed'
