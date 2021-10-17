import datetime
import traceback

from CTFd.utils import get_config
from .db import DBContainer, db
from .docker import DockerUtils
from .routers import Router


class ControlUtil:
    @staticmethod
    def try_add_container(user_id, challenge_id):
        container = DBContainer.create_container_record(user_id, challenge_id)
        try:
            DockerUtils.add_container(container)
        except Exception as e:
            DBContainer.remove_container_record(user_id)
            print(traceback.format_exc())
            return False, 'Docker Creation Error'
        ok, msg = Router.register(container)
        if not ok:
            DockerUtils.remove_container(container)
            DBContainer.remove_container_record(user_id)
            return False, msg
        return True, 'Container created'

    @staticmethod
    def try_remove_container(user_id):
        container = DBContainer.get_current_containers(user_id=user_id)
        if not container:
            return False, 'No such container'
        for _ in range(3):  # configurable? as "onerror_retry_cnt"
            try:
                ok, msg = Router.unregister(container)
                if not ok:
                    return False, msg
                DockerUtils.remove_container(container)
                DBContainer.remove_container_record(user_id)
                return True, 'Container destroyed'
            except Exception as e:
                print(traceback.format_exc())
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
