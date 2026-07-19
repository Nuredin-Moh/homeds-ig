#!/usr/bin/env python3
# Publie le post Homeds du jour sur Instagram + Facebook + LinkedIn (meme legende, memes images).
# Autonome : tourne dans GitHub Actions, independant de tout ordinateur.
# Idempotent par canal (last.json : {"ig": "YYYY-MM-DD", "fb": ..., "li": ...}) :
# si un canal a deja publie aujourd'hui il est saute ; les autres peuvent partir/reessayer.
import json, os, time, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

TOKEN   = os.environ.get("IG_TOKEN", "")     # page access token Meta permanent (sert IG + FB)
IG_ID   = os.environ.get("IG_USER_ID", "")   # instagram business account id
FB_PAGE = os.environ.get("FB_PAGE_ID", "")   # page facebook id (optionnel)
LI_TOKEN = os.environ.get("LI_TOKEN", "")    # token OAuth LinkedIn (scope w_organization_social)
LI_ORG   = os.environ.get("LI_ORG_ID", "")   # id numerique de l'organisation LinkedIn Homeds
V = "v21.0"
BASE = f"https://graph.facebook.com/{V}/"

def api_post(path, params):
    params = dict(params); params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(BASE + path, data=data)
    try:
        return json.load(urllib.request.urlopen(req)), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()[:400]

def api_get(path, params):
    params = dict(params); params["access_token"] = TOKEN
    try:
        return json.load(urllib.request.urlopen(BASE + path + "?" + urllib.parse.urlencode(params))), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()[:400]

try:
    from zoneinfo import ZoneInfo
    today = datetime.now(ZoneInfo("Europe/Zurich")).strftime("%Y-%m-%d")
except Exception:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

state = {}
if os.path.exists("last.json"):
    try: state = json.load(open("last.json"))
    except Exception: state = {}
if "ig" not in state and "last" in state:
    state = {"ig": state.get("last")}

posts = json.load(open("schedule.json", encoding="utf-8"))
todays = [p for p in posts if p["date"] == today]
if not todays:
    print("Aucun post prevu pour", today); raise SystemExit(0)
p = todays[0]; imgs = p["images"]; cap = p["caption"]
print(f"Jour {p.get('jour','?')} - {len(imgs)} image(s) - {today}")

errors = []

# ---------- INSTAGRAM ----------
if not (TOKEN and IG_ID):
    print("IG: IG_TOKEN/IG_USER_ID absents, canal Instagram ignore.")
elif state.get("ig") == today:
    print("IG: deja publie aujourd'hui, saute.")
else:
    if len(imgs) == 1:
        r, err = api_post(f"{IG_ID}/media", {"image_url": imgs[0], "caption": cap})
        cid = r["id"] if r else None
    else:
        children = []; cid = None; err = None
        for u in imgs:
            r, e = api_post(f"{IG_ID}/media", {"image_url": u, "is_carousel_item": "true"})
            if e: err = e; break
            children.append(r["id"]); time.sleep(2)
        if not err:
            r, err = api_post(f"{IG_ID}/media", {"media_type": "CAROUSEL", "children": ",".join(children), "caption": cap})
            cid = r["id"] if r else None
    if err or not cid:
        errors.append("IG media: " + (err or "pas de creation_id")); print("IG ERREUR:", err)
    else:
        ready = False
        for _ in range(24):
            r, e = api_get(cid, {"fields": "status_code"})
            st = (r or {}).get("status_code", "")
            if st == "FINISHED": ready = True; break
            if st == "ERROR": break
            time.sleep(5)
        if not ready:
            errors.append("IG conteneur non pret"); print("IG: conteneur non FINISHED")
        else:
            r, err = api_post(f"{IG_ID}/media_publish", {"creation_id": cid})
            if err: errors.append("IG publish: " + err); print("IG ERREUR publish:", err)
            else: state["ig"] = today; print("IG publie:", r)

# ---------- FACEBOOK ----------
if not (TOKEN and FB_PAGE):
    print("FB: IG_TOKEN/FB_PAGE_ID absents, canal Facebook ignore.")
elif state.get("fb") == today:
    print("FB: deja publie aujourd'hui, saute.")
else:
    if len(imgs) == 1:
        r, err = api_post(f"{FB_PAGE}/photos", {"url": imgs[0], "caption": cap, "published": "true"})
        if err: errors.append("FB photo: " + err); print("FB ERREUR:", err)
        else: state["fb"] = today; print("FB publie:", r)
    else:
        media = []; err = None
        for u in imgs:
            r, e = api_post(f"{FB_PAGE}/photos", {"url": u, "published": "false"})
            if e: err = e; break
            media.append(r["id"]); time.sleep(1)
        if err:
            errors.append("FB upload: " + err); print("FB ERREUR upload:", err)
        else:
            params = {"message": cap}
            for i, mid in enumerate(media):
                params[f"attached_media[{i}]"] = json.dumps({"media_fbid": mid})
            r, err = api_post(f"{FB_PAGE}/feed", params)
            if err: errors.append("FB feed: " + err); print("FB ERREUR feed:", err)
            else: state["fb"] = today; print("FB publie:", r)

# ---------- LINKEDIN ----------
def li_escape(t):
    for ch in "\\<>()[]{}":
        t = t.replace(ch, "\\" + ch)
    return t

def li_headers():
    return {"Authorization": "Bearer " + LI_TOKEN,
            "LinkedIn-Version": "202405",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"}

def li_upload_image(url):
    owner = f"urn:li:organization:{LI_ORG}"
    body = json.dumps({"initializeUploadRequest": {"owner": owner}}).encode()
    req = urllib.request.Request("https://api.linkedin.com/rest/images?action=initializeUpload",
                                 data=body, headers=li_headers())
    val = json.load(urllib.request.urlopen(req))["value"]
    up_url = val["uploadUrl"]; img_urn = val["image"]
    raw = urllib.request.urlopen(url).read()
    put = urllib.request.Request(up_url, data=raw, method="PUT",
                                 headers={"Authorization": "Bearer " + LI_TOKEN})
    urllib.request.urlopen(put)
    return img_urn

if not (LI_TOKEN and LI_ORG):
    print("LI: LI_TOKEN/LI_ORG_ID absents, canal LinkedIn ignore.")
elif state.get("li") == today:
    print("LI: deja publie aujourd'hui, saute.")
else:
    try:
        urns = [li_upload_image(u) for u in imgs]
        if len(urns) == 1:
            content = {"media": {"id": urns[0], "altText": "Homeds"}}
        else:
            content = {"multiImage": {"images": [{"id": u, "altText": "Homeds"} for u in urns]}}
        post = {
            "author": f"urn:li:organization:{LI_ORG}",
            "commentary": li_escape(cap),
            "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
            "content": content,
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        req = urllib.request.Request("https://api.linkedin.com/rest/posts",
                                     data=json.dumps(post).encode(), headers=li_headers())
        urllib.request.urlopen(req)
        state["li"] = today; print("LI publie.")
    except urllib.error.HTTPError as e:
        msg = e.read().decode()[:400]; errors.append("LI: " + msg); print("LI ERREUR:", msg)
    except Exception as e:
        errors.append("LI: " + str(e)[:300]); print("LI ERREUR:", e)

json.dump(state, open("last.json", "w"))
if errors:
    raise SystemExit("Echecs: " + " | ".join(errors))
print("OK - IG + FB + LI a jour pour", today)
