"""
MABUHAY Social Poster — Meta Graph API publishing engine.

Publishes single images and carousels to Instagram, and photos to a Facebook Page,
using a long-lived System-User token. No third-party scheduler needed.

Env vars required (set by the GitHub Action from repo secrets/vars):
    SYSTEM_USER_TOKEN   long-lived Meta system-user token (secret)
    PAGE_ID             Facebook Page ID
    IG_BUSINESS_ID      Instagram Business Account ID

Instagram requires each image to be reachable at a PUBLIC https URL, so images
are served from the repo via raw.githubusercontent.com (see run_scheduler.py).
"""
import os
import time
import requests

GRAPH = "https://graph.facebook.com/v25.0"

TOKEN = os.environ.get("SYSTEM_USER_TOKEN", "")
PAGE_ID = os.environ.get("PAGE_ID", "")
IG_ID = os.environ.get("IG_BUSINESS_ID", "")


class PostError(RuntimeError):
    pass


def _post(path, **params):
    params["access_token"] = TOKEN
    r = requests.post(f"{GRAPH}/{path}", data=params, timeout=60)
    data = r.json()
    if "error" in data:
        raise PostError(f"{path}: {data['error'].get('message')} (code {data['error'].get('code')})")
    return data


def _get(path, **params):
    params["access_token"] = TOKEN
    r = requests.get(f"{GRAPH}/{path}", params=params, timeout=60)
    data = r.json()
    if "error" in data:
        raise PostError(f"{path}: {data['error'].get('message')} (code {data['error'].get('code')})")
    return data


def _wait_finished(container_id, tries=30, delay=4):
    """Poll an IG media container until it is FINISHED (or raise)."""
    for _ in range(tries):
        status = _get(container_id, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise PostError(f"Container {container_id} status ERROR")
        time.sleep(delay)
    raise PostError(f"Container {container_id} not FINISHED after {tries*delay}s")


# ---------- Instagram ----------

def ig_single(image_url, caption):
    """Publish one image to Instagram feed. Returns the published media id."""
    container = _post(f"{IG_ID}/media", image_url=image_url, caption=caption)["id"]
    _wait_finished(container)
    return _post(f"{IG_ID}/media_publish", creation_id=container)["id"]


def ig_carousel(image_urls, caption):
    """Publish a carousel (2-10 images) to Instagram feed. Returns the media id."""
    if not (2 <= len(image_urls) <= 10):
        raise PostError(f"Carousel needs 2-10 images, got {len(image_urls)}")
    children = []
    for url in image_urls:
        cid = _post(f"{IG_ID}/media", image_url=url, is_carousel_item="true")["id"]
        _wait_finished(cid)
        children.append(cid)
    parent = _post(
        f"{IG_ID}/media",
        media_type="CAROUSEL",
        children=",".join(children),
        caption=caption,
    )["id"]
    _wait_finished(parent)
    return _post(f"{IG_ID}/media_publish", creation_id=parent)["id"]


# ---------- Instagram Reels (video) ----------

def ig_reel(video_url, caption, share_to_feed=True):
    """Publish a Reel (single vertical video) to Instagram. Returns the media id.
    Video processing is slower than images, so we poll longer."""
    container = _post(
        f"{IG_ID}/media",
        media_type="REELS",
        video_url=video_url,
        caption=caption,
        share_to_feed="true" if share_to_feed else "false",
    )["id"]
    _wait_finished(container, tries=60, delay=5)   # up to 5 min for transcoding
    return _post(f"{IG_ID}/media_publish", creation_id=container)["id"]


# ---------- Facebook ----------

def fb_video(video_url, caption):
    """Post a video to the Facebook Page (shows in the Page feed / Reels tab).
    Returns the video id."""
    return _post(f"{PAGE_ID}/videos", file_url=video_url, description=caption).get("id")


def fb_photo(image_url, caption, scheduled_unix=None):
    """
    Post a photo to the Facebook Page.
    If scheduled_unix is given, Facebook holds the post natively until then.
    Returns the post/photo id.
    """
    params = {"url": image_url, "caption": caption}
    if scheduled_unix:
        params["published"] = "false"
        params["scheduled_publish_time"] = str(int(scheduled_unix))
    return _post(f"{PAGE_ID}/photos", **params).get("post_id") or _post(f"{PAGE_ID}/photos", **params).get("id")


def fb_photos_multi(image_urls, caption, scheduled_unix=None):
    """
    Post multiple photos as a single Facebook Page post (album-style).
    Uploads each photo unpublished, then creates one feed post referencing them.
    """
    media_fbids = []
    for url in image_urls:
        pid = _post(f"{PAGE_ID}/photos", url=url, published="false")["id"]
        media_fbids.append(pid)
    attached = [{"media_fbid": m} for m in media_fbids]
    import json as _json
    params = {"message": caption, "attached_media": _json.dumps(attached)}
    if scheduled_unix:
        params["published"] = "false"
        params["scheduled_publish_time"] = str(int(scheduled_unix))
    return _post(f"{PAGE_ID}/feed", **params).get("id")


# ---------- Health check ----------

def whoami():
    """Quick sanity check of token + connected accounts. Prints nothing secret."""
    page = _get(PAGE_ID, fields="name")
    ig = _get(IG_ID, fields="username,name")
    limit = _get(f"{IG_ID}/content_publishing_limit").get("data", [{}])[0]
    return {
        "page": page.get("name"),
        "ig": ig.get("username"),
        "ig_name": ig.get("name"),
        "ig_quota_used": limit.get("quota_usage"),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(whoami(), ensure_ascii=False, indent=2))
