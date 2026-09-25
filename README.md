# ARCenal ATS

ARCenal ATS is a standalone FastAPI/PostgreSQL recruitment application prepared for YunoHost. It does not depend on Dolibarr, ARCenal OS, or ARCenal Agent.

## V1 scope

- candidates, job offers, applications, configurable pipeline foundations, and audit trail tables;
- public careers URL at `/recrutement`, with a separate public API for job listings and applications;
- spontaneous applications;
- private document storage outside the web root, with strict file metadata validation;
- YunoHost internal authentication boundary through the `Remote-User` header supplied by SSOwat;
- AACP/1 capability discovery endpoint, deliberately limited to business capabilities;
- YunoHost package skeleton with systemd, Nginx, backup, restore, upgrade, and removal hooks.

## Local development

Use Python 3.11 or later. Install the declared development extra in an isolated environment, then run the checks:

```bash
python -m pip install -e '.[dev]'
ruff check .
mypy src
pytest
uvicorn arcenal_ats.main:app --reload
```

The application requires PostgreSQL. Set an explicit production database URL and an absolute private document directory before deployment. Never map that directory through Nginx.

## Public integration

The default public page is `https://your-domain.example/ats/recrutement`. A client website can link to it directly; no API or script is necessary. The supported public API starts at `/public-api/v1`. It never returns candidate or document data. For an external site, add the exact site origin to the CORS allow-list, then embed `/public/arcenal-jobs.js`; the small widget renders published offers only.

## Security boundary

`/public-api/v1` accepts only public application input. Internal endpoints depend on the identity header injected by SSOwat and must never trust a same-named header arriving directly from the Internet. Documents belong under `/var/lib/arcenal_ats/documents`, not under `/var/www`.

## AACP/1 preparation

The `/aacp/1/capabilities` endpoint advertises constrained business capabilities only. A future authenticated connector must grant each capability explicitly, journal every call, require idempotency keys for writes, and route sensitive HR mutations through an explicit human confirmation step.
