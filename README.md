# homeds-ig — auto-publication social Homeds (août 2026)

Publie automatiquement, 1 post/jour, les carrousels du calendrier éditorial Homeds d'août sur **Instagram + Facebook + LinkedIn**. Tourne dans GitHub Actions (cloud), l'ordinateur peut être éteint.

- `images/` — les slides des carrousels (PNG 1080x1080), servis en URL brute.
- `schedule.json` — planning : 11 posts (dates d'août, images, légendes).
- `publish_daily.py` — publie le post du jour sur les 3 canaux, idempotent par canal (`last.json`).
- `.github/workflows/daily.yml` — cron 3×/jour (~10h17/12h17/15h17 CH).

## Secrets à définir (Settings → Secrets → Actions)
- `IG_TOKEN` — page access token Meta permanent (Homeds), sert IG + FB.
- `IG_USER_ID` — Instagram business account id de Homeds.
- `FB_PAGE_ID` — id de la page Facebook Homeds.
- `LI_TOKEN` — token OAuth LinkedIn (scope `w_organization_social`).
- `LI_ORG_ID` — id numérique de l'organisation LinkedIn Homeds.

Un canal dont les secrets manquent est simplement ignoré (les autres partent quand même).
Test manuel : onglet Actions → « Run workflow ».
