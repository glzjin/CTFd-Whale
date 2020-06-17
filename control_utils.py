import time
import traceback

from flask import session, current_app
from sqlalchemy.sql import and_

from CTFd.models import Challenges, Users
from .db_utils import DBUtils
from .docker_utils import DockerUtils
from .redis_utils import RedisUtils


class ControlUtil:
    @staticmethod
    def try_add_container(user_id, challenge_id):
        port = RedisUtils(app=current_app).get_available_port()
        if not port:
            return False
        container = DBUtils.create_container_record(user_id, challenge_id, port)
        DockerUtils.add_container(container)
        return True

    @staticmethod
    def try_remove_container(user_id):
        container = DBUtils.get_current_containers(user_id=user_id)
        if not container:
            return False
        for _ in range(3):  # configurable? as "onerror_retry_cnt"
            try:
                DockerUtils.remove_container(container)
                DBUtils.remove_container_record(user_id)
                if container.port != 0:
                    redis_util = RedisUtils(app=current_app)
                    redis_util.add_available_port(container.port)
                return True
            except:
                traceback.print_exc()
        return False

    @staticmethod
    def get_container(user_id):
        return DBUtils.get_current_containers(user_id=user_id)

    @staticmethod
    def renew_container(user_id, challenge_id):
        DBUtils.renew_current_container(user_id=user_id, challenge_id=challenge_id)

    @staticmethod
    def check_challenge(challenge_id, user_id):
        user = Users.query.filter_by(id=user_id).first()

        if user.type == "admin":
            Challenges.query.filter(
                Challenges.id == challenge_id
            ).first_or_404()
        else:
            Challenges.query.filter(
                Challenges.id == challenge_id,
                and_(Challenges.state != "hidden", Challenges.state != "locked"),
            ).first_or_404()

    @staticmethod
    def frequency_limit():
        if "limit" not in session:
            session["limit"] = int(time.time())
            return False

        if int(time.time()) - session["limit"] < 60:
            return True

        session["limit"] = int(time.time())
        return False
