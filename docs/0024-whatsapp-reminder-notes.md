# WhatsApp reservation reminder

## Status: shipped

Reservation reminders already support **email** and/or **WhatsApp** (Twilio). Staff uses one action — **Send reminder** (`POST /reservations/{id}/send-reminder`) — and the backend sends to every available channel. Phone-only reservations work when Twilio is configured (email is not required). The same channel logic is used by the autonomous reminder heartbeat.

**Configure** (see `config.env.example`):

| Variable | Purpose |
|----------|---------|
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_WHATSAPP_FROM` | WhatsApp sender (E.164, e.g. `+14155238886`; `whatsapp:` prefix is added if missing) |
| `DEFAULT_PHONE_COUNTRY` | ISO country for normalizing national numbers (default `ES`) |

**Behaviour notes:**

- Phone numbers are normalized to **E.164** before send (`phone_utils.normalize_phone_to_e164`).
- Implementation: `back/app/whatsapp_service.py`. Response includes `email_sent` / `whatsapp_sent` (and optional `to_email` / `to_phone`).
- The service sends a plain-text body today; **production Meta/WhatsApp often requires an approved template** (`ContentSid`) for business-initiated messages — plan for that when leaving the Twilio sandbox.

---

The sections below are **historical design notes** from before shipping. Prefer the status section and code for current behaviour.

---

## 1. Current state (product)

- **Reminder today**: `POST /reservations/{id}/send-reminder` sends **email** (if `customer_email` is set) and/or **WhatsApp** when Twilio is configured. Staff triggers it from the reservations UI.
- **Email reminder link**: When the reservation has a **token** and `PUBLIC_APP_BASE_URL` is set, the message includes `…/reservation?token=…` with the same wording as the confirmation email (“View or change your reservation online”).
- **Reservation model**: `customer_phone` (required), `customer_email` (optional). Phone-only guests are reached via WhatsApp when configured.

---

## 2. Why WhatsApp was added (historical)

- **Reach**: Guests often prefer WhatsApp; open rates are high. If they didn’t give email, we can still remind them via phone.
- **Consistency**: One reminder flow (staff clicks “Send reminder”); backend chooses channel(s): email if present, WhatsApp if phone present and configured.
- **Reduces no-shows**: Same goal as email reminder; more channels = better chance they see it.

---

## 3. Design intent that shipped (historical)

What was recommended and later implemented:

- Keep email reminder; send via WhatsApp when phone is present and WhatsApp is configured.
- One staff action; no separate “Email only” / “WhatsApp only” buttons in v1.
- Normalize `customer_phone` to E.164 at send time.
- Global Twilio env config for v1 (no per-tenant WhatsApp toggle required).

---

## 4. How WhatsApp is sent (historical options → Twilio)

Two main approaches were considered:

| Option | Pros | Cons |
|--------|------|------|
| **WhatsApp Business API (Meta)** | Official, full control, templates. | Business verification, Meta approval, conversation-based pricing. Setup is heavier. |
| **Provider (Twilio, MessageBird, 360dialog, etc.)** | Faster onboarding, often same API under the hood, support. | Monthly/provider cost; dependency on third party. |

**Shipped choice:** Twilio WhatsApp REST API (`whatsapp_service.py`).

**Template reminder:** For “business-initiated” messages outside the sandbox, Meta typically requires **pre-approved message templates**. The current code uses a free-form body suitable for sandbox / sessions; production may need a Content API template (e.g. name, restaurant, date, time, party size).

---

## 5. Design choices (historical → mostly shipped)

| Topic | Outcome |
|--------|---------|
| **When to send WhatsApp** | On “Send reminder” (or heartbeat) when `customer_phone` is present/normalizable and Twilio is configured. |
| **Email + phone both present** | Send **both** when possible. |
| **Phone only** | WhatsApp only; no longer requires email for reminders when WhatsApp is configured. |
| **Phone format** | Normalize to E.164 (`DEFAULT_PHONE_COUNTRY`). |
| **Failure handling** | Per-channel flags; 503 if every attempted channel fails. |
| **Consent / opt-in** | Service reminders for a reservation the guest booked are usually acceptable; legal review per market still recommended for marketing. |

---

## 6. Implementation map (historical outline → code)

### Backend (shipped)

- **Config**: `TWILIO_*` and `DEFAULT_PHONE_COUNTRY` in settings / `config.env.example`.
- **Phone normalization**: `phone_utils.normalize_phone_to_e164`.
- **WhatsApp send**: `whatsapp_service.py` (sync + async wrappers).
- **Reminder endpoint**: `POST /reservations/{id}/send-reminder` returns `email_sent` / `whatsapp_sent` / `to_email` / `to_phone`.
- **Heartbeat**: `reservation_reminder_heartbeat.py` reuses the same channel logic.

### Frontend

- Reservations UI: single “Send reminder” action; response can surface which channels succeeded.

### Template and provider (ops)

- Twilio account + WhatsApp sender; link Meta WABA for production templates as needed.
- Credentials stay in env (not committed).

---

## 7. Summary

- **Shipped**: WhatsApp is an optional second channel next to email for reservation reminders via Twilio.
- **Ops**: Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM` (and optionally `DEFAULT_PHONE_COUNTRY`); see `config.env.example`.
- **Production caveat**: Plain-text body may need a Meta-approved template outside the Twilio sandbox.
