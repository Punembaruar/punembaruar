# Deploy i PunëMbaruar v1.1 në Render

## Për test publik
1. Krijo llogari Render.
2. Ngarko projektin në një Git repository që kontrollon ti.
3. Në Render zgjidh Blueprint ose Web Service dhe përdor `render.yaml`.
4. Vendos environment variables:
   - DATABASE_URL = PostgreSQL/Supabase URL
   - ADMIN_USERNAME = username privat
   - ADMIN_PASSWORD = password i fortë
5. Deploy.
6. Kontrollo `/health`.
7. Hape `/` dhe `/admin`.

Mos përdor SQLite për të dhëna reale në hosting ephemeral, sepse file-i lokal mund të humbasë gjatë redeploy/restart.
