from __future__ import annotations

from src.session_manager import SessionManager


def main() -> None:
    manager = SessionManager(30)
    created = manager.create_session("alpha")
    valid = manager.is_valid("alpha")
    print(f"created={created} valid={valid} count={manager.session_count()}")


if __name__ == "__main__":
    main()
