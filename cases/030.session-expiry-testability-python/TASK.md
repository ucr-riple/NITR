## Task

Implement a small `SessionManager`.

A session has an id and a TTL in seconds.
Support:
- creating a session
- checking whether a session is currently valid
- refreshing a valid session so its validity window restarts
- removing a session

Rules:
1. A session is valid immediately after creation.
2. A session becomes invalid once the elapsed time since creation or the most recent refresh reaches the TTL.
3. Refreshing a missing or expired session should fail.
4. Removing a session makes later validity checks fail.

Keep the implementation small and readable.
