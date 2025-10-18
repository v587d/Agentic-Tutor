Below are concise, actionable instructions to help an AI coding agent be productive in the Agentic Tutor codebase.

1) Big-picture architecture (what to change and where)
- Backend: FastAPI app entry in `src.api.app.create_app` and server runner `src.api.__main__`.
- AI layer: `src.agents.host_agent.HostAgent` wraps the external DashScope model and implements message build/load/persist logic. Changes that affect model behavior (prompts, streaming, usage recording) belong here.
- Persistence: SQLAlchemy async models in `src.db.models` and DB manager in `src.db.db` (singleton pattern). Use `db_manager.session` for async sessions.
- Repositories: Data-access helpers in `src.repositories/*` (e.g. `chat_repo.py`, `user_repo.py`, `persona_repo.py`). Prefer adding business logic there rather than in route handlers.
- API: Routers under `src.api.routers/*` (chat, user, session). Dependency factories in `src.api.deps` (notably `get_agent`).

2) Startup / dev workflows (commands and environment)
- Development server: `python -m src.api` (uses `uvicorn` with reload; see `src/api/__main__.py`).
- Production uvicorn example (non-reload): `uvicorn src.api.app:create_app --host 0.0.0.0 --port 80`.
- Environment: `.env` style vars read by `src.config.settings`. Important vars: `API_KEY`, `API_BASE`, `MODEL_NAME`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `DATABASE_URL`.
- DB initialization: the app initializes DB on startup via `await db_manager.initialize()`; running `python -m src.api` will create tables automatically.

3) Project-specific conventions and patterns
- Async-first: Database access uses SQLAlchemy async engine + async_sessionmaker; repository functions are async and must be awaited.
- DB manager singleton: `src.db.db.db_manager` is a singleton with `session` property returning an AsyncSession (property triggers synchronous initialization if needed).
- Persona prompt composition: `Persona.compile_profile_prompt()` in `src.db.models` builds structured system/assistant prompts from the JSON `profile` field — modify here to change persona injection.
- HostAgent responsibilities: Build messages, load persona & history, persist user/assistant messages, and call `DashScopeChatModel`. Keep I/O (DB, model calls) in HostAgent and repositories; keep routers thin.
- Streaming: `HostAgent.stream_reply` yields generator chunks from model; `src.api.routers.chat.chat_stream` wraps it in SSE with `StreamingResponse`.
- Token handling: JWT is created/validated in `src.utils.security` (uses `SECRET_KEY` and HS256). When adding auth endpoints, follow `create_access_token` and `verify_token` patterns.

4) Common code edits and where to place them
- Add new DB columns/models: modify `src.db.models`, then no separate migrations are present — the app auto-creates tables on startup. For schema changes that break existing data, add a migration strategy (not present).
- New API route: add router under `src.api.routers`, include it in `src.api.app.create_app`.
- New repository logic: add helpers to `src.repositories` and call them in routers or agents.
- Integrating a new model provider: wrap provider-specific code inside `src.agents` and keep `HostAgent` thin; follow the existing pattern with `model(messages)` and stream support.

5) Tests / lint / quick checks
- No tests included in repo. For quick sanity, run the dev server `python -m src.api` and exercise `POST /chat/stream` (the frontend in `static/pages/chat.html` is a helpful manual test). 

6) Safety, validation, and important checks to preserve
- Session keys: `src.api.routers.chat.validate_session_key` contains specific format and TTL checks — keep compatibility when changing session semantics.
- Forbidden content checks: chat router filters a small blacklist. If you expand filters, update this function.
- DB PRAGMA tuning: `src.db.db._sqlite_on_connect` sets WAL and foreign_keys; keep this for SQLite performance and referential integrity.

7) Useful snippets (copyable examples)
- Create HostAgent and request a streamed reply (use in background tasks or deps):
  - from `src.api.deps` use `async with get_agent(session_id=..., user_id=...) as agent: async for chunk in agent.stream_reply(text): ...`
- Persist a message using the repo:
  - `await src.repositories.chat_repo.add_message(session_pk, role, content, meta={"agent_name": "X"})`

8) Files to inspect when debugging common problems
- App / startup: `src/api/app.py`, `src/api/__main__.py`
- Model integration: `src/agents/host_agent.py`
- DB and models: `src/db/db.py`, `src/db/models.py`
- Repositories: `src/repositories/*.py`
- Auth and security: `src/utils/security.py`, `src/api/routers/auth.py`

If anything in these notes is unclear or you'd like the file to emphasize different examples, tell me which part and I'll iterate.
