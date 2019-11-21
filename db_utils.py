import datetime
import uuid

from .models import WhaleConfig, WhaleContainer

from CTFd.models import (
    db
)


class DBUtils:
    @staticmethod
    def get_all_configs():
        configs = WhaleConfig.query.all()
        result = {}

        for c in configs:
            result[str(c.key)] = str(c.value)

        return result

    @staticmethod
    def save_all_configs(configs):
        for c in configs:
            q = db.session.query(WhaleConfig)
            q = q.filter(WhaleConfig.key == c[0])
            record = q.one_or_none()

            if record:
                record.value = c[1]
                db.session.commit()
            else:
                config = WhaleConfig(key=c[0], value=c[1])
                db.session.add(config)
                db.session.commit()
        db.session.close()

    @staticmethod
    def create_new_container(user_id, challenge_id, flag, port=0):
        uuid_code = uuid.uuid4()
        container = WhaleContainer(user_id=user_id, challenge_id=challenge_id, flag=flag, uuid=uuid_code, port=port)
        db.session.add(container)
        db.session.commit()
        db.session.close()

        return str(uuid_code)

    @staticmethod
    def get_current_containers(user_id):
        q = db.session.query(WhaleContainer)
        q = q.filter(WhaleContainer.user_id == user_id)
        records = q.all()
        if len(records) == 0:
            return None

        return records[0]

    @staticmethod
    def get_container_by_port(port):
        q = db.session.query(WhaleContainer)
        q = q.filter(WhaleContainer.port == port)
        records = q.all()
        if len(records) == 0:
            return None

        return records[0]

    @staticmethod
    def remove_current_container(user_id):
        q = db.session.query(WhaleContainer)
        q = q.filter(WhaleContainer.user_id == user_id)
        # records = q.all()
        # for r in records:
        #     pass

        q.delete()
        db.session.commit()
        db.session.close()

    @staticmethod
    def renew_current_container(user_id, challenge_id):
        q = db.session.query(WhaleContainer)
        q = q.filter(WhaleContainer.user_id == user_id)
        q = q.filter(WhaleContainer.challenge_id == challenge_id)
        records = q.all()
        if len(records) == 0:
            return

        configs = DBUtils.get_all_configs()
        timeout = int(configs.get("docker_timeout", "3600"))

        r = records[0]
        r.start_time = r.start_time + datetime.timedelta(seconds=timeout)

        if r.start_time > datetime.datetime.now():
            r.start_time = datetime.datetime.now()

        r.renew_count += 1
        db.session.commit()
        db.session.close()

    @staticmethod
    def get_all_expired_container():
        configs = DBUtils.get_all_configs()
        timeout = int(configs.get("docker_timeout", "3600"))

        q = db.session.query(WhaleContainer)
        q = q.filter(WhaleContainer.start_time < datetime.datetime.now() - datetime.timedelta(seconds=timeout))
        return q.all()

    @staticmethod
    def get_all_alive_container():
        configs = DBUtils.get_all_configs()
        timeout = int(configs.get("docker_timeout", "3600"))

        q = db.session.query(WhaleContainer)
        q = q.filter(WhaleContainer.start_time >= datetime.datetime.now() - datetime.timedelta(seconds=timeout))
        return q.all()

    @staticmethod
    def get_all_container():
        q = db.session.query(WhaleContainer)
        return q.all()

    @staticmethod
    def get_all_alive_container_page(page_start, page_end):
        configs = DBUtils.get_all_configs()
        timeout = int(configs.get("docker_timeout", "3600"))

        q = db.session.query(WhaleContainer)
        q = q.filter(WhaleContainer.start_time >= datetime.datetime.now() - datetime.timedelta(seconds=timeout))
        q = q.slice(page_start, page_end)
        return q.all()

    @staticmethod
    def get_all_alive_container_count():
        configs = DBUtils.get_all_configs()
        timeout = int(configs.get("docker_timeout", "3600"))

        q = db.session.query(WhaleContainer)
        q = q.filter(WhaleContainer.start_time >= datetime.datetime.now() - datetime.timedelta(seconds=timeout))
        return q.count()
