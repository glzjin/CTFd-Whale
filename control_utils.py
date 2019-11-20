import time

from CTFd.models import Challenges, Users
from .db_utils import DBUtils
from .docker_utils import DockerUtils
from sqlalchemy.sql import and_
from flask import session
from .redis_utils import RedisUtils

class ControlUtil:
    @staticmethod
    def add_container(app, user_id, challenge_id, flag, port=0):
        uuid_code = DBUtils.create_new_container(user_id, challenge_id, flag, port)
        DockerUtils.add_new_docker_container(app=app, user_id=user_id, challenge_id=challenge_id, flag=flag, uuid_code=uuid_code)

    @staticmethod
    def remove_container(app, user_id):
        docker_result = DockerUtils.remove_current_docker_container(app, user_id)
        if docker_result:
            container = ControlUtil.get_container(user_id)
            port = container.port
            DBUtils.remove_current_container(user_id)
            if port != 0:
                redis_util = RedisUtils(app)
                redis_util.add_available_port(port)

        return docker_result

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
