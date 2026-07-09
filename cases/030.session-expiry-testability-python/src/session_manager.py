from __future__ import annotations

from dataclasses import dataclass

from src.time_source import SystemTimeSource, TimeSource


@dataclass
class SessionRecord:
    session_id: str
    created_at_seconds: int
    last_started_at_seconds: int


class SessionManager:
    def __init__(
        self,
        ttl_seconds: int,
        time_source: TimeSource | None = None,
    ) -> None:
        self._ttl_seconds = ttl_seconds
        self._time_source = time_source or SystemTimeSource()
        self._sessions: dict[str, SessionRecord] = {}

    def create_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            return False

        now_seconds = self._time_source.now_seconds()
        self._sessions[session_id] = SessionRecord(
            session_id=session_id,
            created_at_seconds=now_seconds,
            last_started_at_seconds=now_seconds,
        )
        return True

    def is_valid(self, session_id: str) -> bool:
        if session_id not in self._sessions:
            return False

        # TODO: implement expiration logic.
        return True

    def refresh_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session is None:
            return False

        # TODO: refresh should fail for expired sessions and restart the TTL window.
        session.last_started_at_seconds = self._time_source.now_seconds()
        return True

    def remove_session(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def session_count(self) -> int:
        return len(self._sessions)
