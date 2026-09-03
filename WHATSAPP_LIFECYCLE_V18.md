# v1.8 — WhatsApp lifecycle

WhatsApp është kanal njoftimi dhe rikthimi; oferta, chat-i, statusi i punës dhe review bëhen në PunëMbaruar.

Eventet kryesore:
1. Biznesi: NEW_REQUEST → link direkt te kërkesa/oferta në web.
2. Klienti: NEW_OFFER → link te ofertat. Ofertat mund të grupohen për të shmangur spam.
3. Biznesi: OFFER_ACCEPTED.
4. Klient/Biznes: UNREAD_CHAT vetëm për mesazh të rëndësishëm/palexuar.
5. Klient + Biznes: JOB_CONFIRMATION pas afatit të punës.
6. Klienti: REVIEW pasi puna konfirmohet.

Konfirmimi i punës:
- YES + YES = COMPLETED → verified review lejohet.
- NO + NO = NOT_COMPLETED.
- STILL_IN_PROGRESS nga njëra palë = IN_PROGRESS.
- përgjigje kontradiktore = DISPUTED → Admin review.
- vetëm një përgjigje = AWAITING_OTHER_PARTY.

Meta WhatsApp Business API dhe template-t reale konfigurohen pas deploy-it; ky version përmban queue/workflow.
