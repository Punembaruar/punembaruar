# PunëMbaruar v1.5 — WhatsApp + Chat + Moderation

## WhatsApp
The product flow is:
1. Client publishes a request.
2. Matching ranks eligible APPROVED + active providers.
3. Notification queue selects the configured batch.
4. Provider receives a WhatsApp notification with a direct request/offer link.
5. Provider opens PunëMbaruar and submits the offer on the website.
6. Client/provider continue conversation in PunëMbaruar chat.
7. New important chat activity can trigger a WhatsApp notification back to the relevant party.

The app retains the existing WhatsApp queue/preparation. Real outbound WhatsApp messages require official Meta WhatsApp Business Platform credentials and approved message templates after deployment. No unofficial WhatsApp automation is used.

## Website chat
Chat stays inside PunëMbaruar so the marketplace keeps job context, moderation capability and history. WhatsApp is a notification/return channel, not a replacement for the marketplace chat.

## Moderation added in v1.5
- Report professional/request/offer/message
- Admin report queue
- Immediate provider suspension
- Immediate request suspension
- Immediate offer suspension
- Job outcomes: COMPLETED / NO_SHOW / CANCELLED / DISPUTED
- No-show does not count as a completed job

## Provider eligibility
Only providers that are APPROVED and active should be eligible for matching and WhatsApp request notifications.
