# PunëMbaruar v1.8 — RENDER READY

# PunëMbaruar v1.2 — Automotive Launch Candidate

Launch-focused evolution of v1.1 after benchmarking Openbay's official marketplace flow.

## Main launch proposition
**Ke problem me makinën? Përshkruaje një herë dhe merr oferta nga serviset.**

## Automotive entry points
- 🔧 Kam problem / Dua riparim
- 🔩 Kërkoj pjesë
- 🔍 Dua diagnostikim
- 🛞 Goma / Gomisteri
- ❄️ Kondicioner
- 🚗 Karroceri / Bojë

## New launch logic
- Richer vehicle/request information.
- Shops can quote as FIXED, RANGE, or DIAGNOSTIC.
- Optional quote breakdown: parts, labor, warranty, estimated time and availability.
- Keeps existing low-cost matching, WhatsApp queue, profiles, reviews, Garage, dashboards, admin analytics and CSV export.
- General Services architecture remains in the database, but the public launch page is intentionally automotive-first.

## Why this matters
A repair shop cannot responsibly give an exact repair price for every symptom without seeing the vehicle. v1.2 therefore supports diagnostic and range quotes instead of forcing fake precision.

See `OPENBAY_ANALYSIS.md` for the product decisions taken from the benchmark.


See `LAUNCH_STRATEGY.md` for product decisions.


## v1.4
Provider self-registration now uses an approval workflow. New providers are inactive until approved. See `PROVIDER_VERIFICATION.md`.


### v1.4.1 verification gate
Minimum 3 verification photos + NIPT + responsible person + address are required before submission. Video is optional unless Admin requests it.


## v1.5
Added moderation/reporting, suspension controls, no-show/cancelled/disputed outcomes, and formalized the official Meta WhatsApp notification → website offer/chat workflow. See `WHATSAPP_CHAT_MODERATION.md`.


## v1.6
5-request free trial + auditable credits + Admin-controlled fake/spam/duplicate decisions + automatic refunds.


## v1.7
Added Admin-managed automotive category catalog with add/edit/activate/deactivate/soft-delete and 20 seeded launch categories. Existing v1.6 trust/trial and core platform features retained.


## v1.8
WhatsApp lifecycle queue for provider/client events, grouped client offer alerts, unread-chat alerts, dual client/provider job confirmation, dispute detection and verified-review eligibility. v1.7 categories and earlier trust/moderation features retained.
