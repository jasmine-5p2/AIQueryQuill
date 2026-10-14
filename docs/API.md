# API reference

Base URL locally: `http://localhost:4000`. Authenticated requests use `Authorization: Token <token>` and JSON content type.

## Authentication

`POST /api/auth/register/` and `POST /api/auth/login/` accept `{"username":"...","password":"..."}`. Success returns `{ "token": "...", "username": "..." }`. Passwords need at least 8 characters and usernames at least 3.

## Conversations

- `GET /api/chats/` returns only the signed-in user's sessions.
- `POST /api/chats/` accepts optional `{ "title": "..." }`.
- `GET /api/chats/{id}/messages/` returns chronological messages. Non-owned ids return 404.
- `DELETE /api/chats/{id}/` deletes an owned session and its messages; otherwise 404.

## Stream a response

`POST /api/chat/` accepts `{ "chat_id": 1, "message": "...", "model": "gemini-2.0-flash", "temperature": 0.7 }`. `chat_id` may be omitted to create a session. The response is Server-Sent Events: each `data:` line contains JSON with `text` (a streamed fragment), `done` (completion and chat id), or `error` (human-readable failure). Input length is capped at 12,000 characters and temperature is clamped to 0–1.

## Health

`GET /api/health/` checks Django. `GET /gateway-health` checks the Express process. Neither endpoint checks database connectivity or Gemini availability.
