import shelve
from typing import Any


class SessionStorage:

    def __init__(
            self,
            use_local_cache: bool = True,
            get_sessions=None,
            get_session=None,
            set_session=None,
            delete_session=None,
    ):

        self.get_sessions = get_sessions
        self.get_session = get_session
        self.set_session = set_session
        self.delete_session = delete_session

        self.use_local_cache = use_local_cache or os.environ.get(
            "AUTH0_USE_LOCAL_CACHE")

        @property
        def use_local_cache(self):
            return self._use_local_cache

        @use_local_cache.setter
        def use_local_cache(self, val):
            self._use_local_cache = val

    def _get_stored_sessions(self) -> Any:
        if (self.use_local_cache):
            with shelve.open(".sessions_cache") as sessions:
                return list(sessions.keys())
        else:
            return self.get_session()

    def _get_stored_session(self, user_id: str) -> str:
        if (self.use_local_cache):
            with shelve.open(".sessions_cache") as sessions:
                return sessions.get(user_id)
        else:
            return self.get_session()

    def _set_stored_session(self, user_id, encrypted_session_data):
        if (self.use_local_cache):
            with shelve.open(".sessions_cache") as sessions:
                sessions[user_id] = encrypted_session_data
                sessions.sync()
        else:
            self.set_session()

    def _delete_stored_session(self, user_id):
        if (self.use_local_cache):
            with shelve.open(".sessions_cache") as sessions:
                if user_id in sessions:
                    del sessions[user_id]
                    sessions.sync()
        else:
            self.del_session()
