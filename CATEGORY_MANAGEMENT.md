# PunëMbaruar v1.7 — Menaxhimi i kategorive

Admin ka katalog të menaxhueshëm të kategorive automotive.

Default:
Servise mekanike; pjesë të reja; pjesë të përdorura; elektroauto; diagnostikë;
gomisteri; kondicioner; karroceri; bojë; kambio; diesel/injektorë; marmita;
xhama; bateri; disqe/goma; autoçelësa; aksesore; tapiceri; detailing/lavazh;
karrotrec/asistencë.

Admin mund të:
- shtojë kategori;
- ndryshojë emër, slug, prioritet dhe tip;
- aktivizojë/çaktivizojë kategori;
- “heqë” kategori me soft-delete (çaktivizim), që të mos prishet historia e kërkesave.

Kategoritë aktive ekspozohen te endpoint-i publik `/api/categories/manageable`.
