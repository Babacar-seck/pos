# Hardware printing (kitchen + receipt bridge)

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/317
- **317**

## Problem / goal

POS only supports `window.print()` (browser dialog). There is no restaurant-LAN print agent, `/api/print-jobs` API, or WebSocket print bridge, so staff cannot silently send kitchen/receipt jobs to a thermal printer. Design notes already exist in `docs/PRINTING.md` (not implemented).

## High-level instructions for coder

- **Phase 0:** Confirm Option A (WebApp Hardware Bridge on staff LAN) vs Option C (headless agent polling backend) as the default; record a short ADR in docs.
- **MVP (Phase 1):** Backend `POST /api/print-jobs` (tenant-scoped: `job_type` kitchen|receipt, order/payload). Local agent registers tenant/device, receives jobs (WS or poll), maps printer role → IP/name, sends ESC/POS (e.g. `:9100` or CUPS). Frontend kitchen / receipt / Factura actions call the print-job API first; fall back to `window.print()` with a visible “bridge offline” warning.
- Auth: agent must authenticate per tenant; do not expose unauthenticated raw print endpoints (`docs/SECURITY-REVIEW.md`).
- Align with `docs/0015-kitchen-display.md` and `docs/0017-billing-customers-factura.md`. Cash-drawer kick and label/ZPL printers are out of scope for this slice.
- Add install/runbook under `docs/` (setup, printer IP, health / last-seen, troubleshooting).
- `CHANGELOG.md` entry; append **Testing instructions**. Prefer a LAN smoke path that proves one kitchen ticket without a browser print dialog when the bridge is up.

## Implementation notes (coder)

- **ADR:** Option **C** (cloud queue + LAN poll agent) is the default; Option A deferred — `docs/0070-hardware-printing.md`.
- Migration `20260726174000_print_jobs.sql`: `print_agent` + `print_job`.
- Backend: `print_service.py` / `print_routes.py` — staff `POST/GET /print-jobs`, `/print-jobs/status`, `/tenant/print-agents`; agent `POST /print-agent/heartbeat`, `GET /print-agent/jobs`, `POST .../complete` (Bearer token, SHA-256 stored).
- Agent script: `scripts/print-agent/print_agent.py` (ESC/POS TCP `:9100`, `PRINT_AGENT_DRY_RUN=1`).
- Frontend: Settings → Printing; Orders kitchen + invoice try bridge first then `window.print()` + toast; `PrintBridgeService`.
- Tests: `back/tests/test_print_jobs.py`.

## Testing instructions

1. **Migrate:** `docker compose … exec back python -m app.migrate --check` — schema includes `20260726174000`.
2. **Unit:** `docker compose … exec back python3 -m pytest tests/test_print_jobs.py -q` — expect 5 passed (agent create/poll/complete, tenant isolation, 401 without token, SaaS exempt `/print-agent`).
3. **Settings UI:** Login as owner → Settings → Printing → create agent with device id → copy one-time token; status shows offline until agent heartbeats.
4. **Dry-run agent:**  
   `PRINT_AGENT_API_BASE=http://127.0.0.1:4202/api PRINT_AGENT_TOKEN=<token> PRINT_AGENT_DRY_RUN=1 python3 scripts/print-agent/print_agent.py`  
   Then Orders → open order → **Print kitchen ticket** (or Print invoice). Expect toast “Sent to print agent”; `tmp/print-agent-last.txt` contains ticket text; no browser print dialog.
5. **Offline fallback:** Stop the agent for >60s → print again → toast “Print bridge offline” and browser print dialog appears.
6. **Security:** `curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:4202/api/print-agent/jobs` → `401`.
7. **Smoke:** `BASE_URL=http://127.0.0.1:4202 npm run test:landing-version --prefix front` (exit 0). Docs: `docs/0070-hardware-printing.md`, `docs/PRINTING.md` status, `docs/testing.md`.
