from flask_redis import FlaskRedis
from redis.exceptions import LockError


class LockUtils:
    def __init__(self, app, user_id):
        self.redis_client = FlaskRedis(app)
        self.key = 'ctfd_whale_lock-' + str(user_id)
        self.lock = None

    def acquire(self):
        lock = self.redis_client.lock(name=self.key, timeout=10)

        if not lock.acquire(blocking=True, blocking_timeout=0.5):
            return False

        self.lock = lock
        return True

    def release(self):
        if self.lock is None:
            return False

        try:
            self.lock.release()

            return True
        except LockError:
            return False
