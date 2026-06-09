# Connectors And Channels

## 1. Connector Decision

Hermes owns the connector runtime contract. Feishu, WeChat, QQ, web, and CLI are
thin adapters.

The platform adapter sends and receives messages. Hermes owns the state machine.

## 2. Core Contract

Required endpoints:

- `POST /social/turn`
- `POST /jobs/event`
- `POST /media/plan-send`

The connector sends:

- channel;
- target id;
- message text;
- platform metadata when safe.

Hermes returns:

- direct reply or quick ACK;
- job plan;
- route;
- media envelope;
- owner-confirmation requirement;
- safe progress state.

## 3. Feishu

Feishu is the company operations surface.

Allowed first:

- receive bot messages;
- send replies;
- read tasks, documents, Bitable, calendars when permissions are configured;
- send summaries and reminders;
- create owner approval cards.

Requires approval:

- write task updates;
- approve expenses;
- change HR or compensation data;
- send external commitments;
- modify legal or contract documents.

## 4. WeChat

WeChat is personal and low-risk.

Allowed:

- personal reminders;
- quick capture;
- lightweight companion replies;
- selected important alerts.

Not allowed:

- company approvals;
- money movement;
- HR/legal/company-wide commands;
- trading actions.

## 5. QQ

QQ has two separated routes:

- official bot route for lower protocol risk;
- personal scan bridge route only as experimental owner-controlled access.

QQ must not become a company-write channel.

## 6. Media Delivery

Connectors must not send raw generated image paths as final text.

Flow:

```text
worker creates media
  -> connector calls /media/plan-send
  -> Hermes returns send_image_file, upload_then_send, or send_text_fallback
  -> connector delivers
  -> connector reports /jobs/event
```

