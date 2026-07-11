"""
Scheduler runner — fired by GitHub Actions on a cron.

Reads calendar.json, publishes any post whose time has arrived and that hasn't
been posted yet (tracked in posted.json), then the Action commits posted.json back.

Image URLs are built from IMAGE_BASE (set by the workflow to the repo's raw URL),
so Instagram can fetch them publicly.
"""
import json
import os
import sys
from datetime import datetime, timezone

import poster

CAL = "calendar.json"
STATE = "posted.json"
IMAGE_BASE = os.environ.get("IMAGE_BASE", "").rstrip("/")


def load(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def save(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def img_url(name):
    return f"{IMAGE_BASE}/{name}"


def due(post, now):
    when = datetime.fromisoformat(post["datetime"])
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when <= now


def publish(post):
    caption = post["caption"]
    urls = [img_url(n) for n in post["images"]]
    platforms = post.get("platforms", ["instagram", "facebook"])
    results = {}
    if "instagram" in platforms:
        if post["type"] == "carousel":
            results["instagram"] = poster.ig_carousel(urls, caption)
        else:
            results["instagram"] = poster.ig_single(urls[0], caption)
    if "facebook" in platforms:
        if post["type"] == "carousel" and len(urls) > 1:
            results["facebook"] = poster.fb_photos_multi(urls, caption)
        else:
            results["facebook"] = poster.fb_photo(urls[0], caption)
    return results


def main():
    if not IMAGE_BASE:
        print("ERROR: IMAGE_BASE not set", file=sys.stderr)
        sys.exit(1)

    calendar = load(CAL, [])
    posted = load(STATE, {"done": []})
    done = set(posted.get("done", []))
    now = datetime.now(timezone.utc)

    fired = []
    for post in calendar:
        pid = post["id"]
        if pid in done:
            continue
        if not due(post, now):
            continue
        try:
            res = publish(post)
            done.add(pid)
            fired.append(pid)
            print(f"POSTED {pid}: {res}")
        except poster.PostError as e:
            print(f"FAILED {pid}: {e}", file=sys.stderr)
            # do not mark done → retried next run

    posted["done"] = sorted(done)
    save(STATE, posted)

    if fired:
        print(f"Published {len(fired)} post(s): {', '.join(fired)}")
    else:
        print("Nothing due.")


if __name__ == "__main__":
    main()
