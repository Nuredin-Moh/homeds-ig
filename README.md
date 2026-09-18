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

## LinkedIn (depuis le 18.09.2026)

Publication automatique aussi sur la Page LinkedIn Homeds (`urn:li:organization:118904187`),
via l'app « Homeds Auto Posting » (Community Management API, Development Tier).

- Secrets GitHub : `LI_TOKEN` (jeton OAuth, **valable 2 mois**) et `LI_ORG_ID`.
- ⚠️ **Le jeton expire le 16.11.2026** puis tous les ~2 mois. Pour le renouveler, une seule commande :
  `bash ~/.homeds-linkedin/renouveler.sh` (ouvre LinkedIn, un clic « Autoriser », et le secret GitHub est mis a jour).
  Sans renouvellement, seul LinkedIn s'arrete : Instagram et Facebook continuent.
- `LI_START` (defaut `2026-10-30`) : avant cette date les posts LinkedIn sont deja programmes a la main
  sur la Page, le script les saute pour eviter les doublons.
