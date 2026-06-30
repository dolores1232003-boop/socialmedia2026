"""Entrypoint del cron de GitHub Actions: publica los posts programados que ya están due."""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from meta_api import MetaApiError, build_media_url
from publish import publish_facebook_post, publish_instagram_post

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEDULED_POSTS_PATH = REPO_ROOT / "data" / "scheduled_posts.json"


def load_posts():
    if not SCHEDULED_POSTS_PATH.exists():
        return []
    with open(SCHEDULED_POSTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_posts(posts):
    with open(SCHEDULED_POSTS_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
        f.write("\n")


def is_due(scheduled_datetime_str, now):
    scheduled_dt = datetime.fromisoformat(scheduled_datetime_str.replace("Z", "+00:00"))
    return scheduled_dt <= now


def publish_entry(entry):
    media_url = None
    if entry.get("media_path"):
        media_url = build_media_url(entry["media_path"])

    platform = entry["platform"]
    if platform == "instagram":
        return publish_instagram_post(
            caption=entry.get("caption", ""),
            media_url=media_url,
            media_type=entry.get("media_type", "IMAGE"),
        )
    elif platform == "facebook":
        return publish_facebook_post(message=entry.get("caption", ""), media_url=media_url)
    else:
        raise MetaApiError(f"Plataforma desconocida: {platform!r} (usa 'instagram' o 'facebook')")


def process_posts():
    posts = load_posts()
    now = datetime.now(timezone.utc)
    changed = False

    for entry in posts:
        if entry.get("status") != "scheduled":
            continue
        if not is_due(entry["scheduled_datetime"], now):
            continue

        print(f"Publicando entrada {entry.get('id')} en {entry.get('platform')}...")
        try:
            post_id = publish_entry(entry)
            entry["status"] = "posted"
            entry["posted_at"] = now.isoformat()
            entry["platform_post_id"] = post_id
            entry["error"] = None
            print(f"  OK -> id={post_id}")
        except MetaApiError as exc:
            entry["status"] = "failed"
            entry["error"] = str(exc)
            print(f"  FALLÓ: {exc}")
        changed = True

    if changed:
        save_posts(posts)

    return changed


def commit_and_push():
    bot_name = "socialmedia2026-bot"
    bot_email = "actions@users.noreply.github.com"
    commands = [
        ["git", "config", "user.name", bot_name],
        ["git", "config", "user.email", bot_email],
        ["git", "add", str(SCHEDULED_POSTS_PATH)],
        ["git", "commit", "-m", "Update post status [skip ci]"],
    ]
    for cmd in commands:
        subprocess.run(cmd, cwd=REPO_ROOT, check=True)

    push = subprocess.run(["git", "push"], cwd=REPO_ROOT)
    if push.returncode != 0:
        print("Push rechazado, intentando rebase y reintentar una vez...")
        subprocess.run(["git", "pull", "--rebase"], cwd=REPO_ROOT, check=True)
        subprocess.run(["git", "push"], cwd=REPO_ROOT, check=True)


def main():
    changed = process_posts()
    if changed:
        commit_and_push()
    else:
        print("No hay publicaciones pendientes que ya estén due.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 - queremos que el log de Actions sea legible
        print(f"Error fatal en check_scheduled.py: {exc}")
        sys.exit(1)
