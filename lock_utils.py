from CTFd.cache import cache


class LockUtils:
    @staticmethod
    def acquire_lock(user_id):
        key = 'ctfd-whale-lock-' + str(user_id)

        if cache.get(key) is not None:
            return False

        cache.set(key, '1', timeout=10)

        return True

    @staticmethod
    def release_lock(user_id):
        key = 'ctfd-whale-lock-' + str(user_id)

        if cache.get(key) is None:
            return False

        cache.delete(key)

        return True
