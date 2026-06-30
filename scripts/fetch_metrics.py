"""Entrypoint del cron diario: trae métricas de Meta, las guarda y regenera el reporte.

Las métricas de Insights de Meta cambian de nombre con cierta frecuencia. Por eso este
script pide cada métrica de forma individual y, si una falla, la salta y sigue con las
demás en vez de abortar todo el run.
"""

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from meta_api import MetaApiError, fb_page_id, graph_get, ig_business_account_id

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEDULED_POSTS_PATH = REPO_ROOT / "data" / "scheduled_posts.json"
METRICS_CSV_PATH = REPO_ROOT / "data" / "metrics_history.csv"
REPORT_PATH = REPO_ROOT / "reports" / "REPORT.md"

CSV_HEADER = ["date", "platform", "scope", "post_id", "metric_name", "value"]

IG_ACCOUNT_METRICS = ["reach", "profile_views", "follower_count"]
IG_POST_METRICS = ["reach", "likes", "comments", "saved", "shares"]
FB_PAGE_METRICS = ["page_impressions", "page_engaged_users"]
FB_POST_METRICS = ["post_impressions", "post_engaged_users"]


def load_posted_entries():
    if not SCHEDULED_POSTS_PATH.exists():
        return []
    with open(SCHEDULED_POSTS_PATH, "r", encoding="utf-8") as f:
        posts = json.load(f)
    return [p for p in posts if p.get("status") == "posted" and p.get("platform_post_id")]


def fetch_metric(object_id, metric_name, extra_params=None):
    params = {"metric": metric_name}
    if extra_params:
        params.update(extra_params)
    try:
        result = graph_get(f"{object_id}/insights", params)
    except MetaApiError as exc:
        print(f"  [omitida] métrica '{metric_name}' para {object_id}: {exc}")
        return None

    data = result.get("data", [])
    if not data:
        return None
    values = data[0].get("values", [])
    if values:
        return values[-1].get("value")
    return data[0].get("value")


def collect_account_metrics(today):
    rows = []

    ig_id = None
    try:
        ig_id = ig_business_account_id()
    except MetaApiError as exc:
        print(f"IG_BUSINESS_ACCOUNT_ID no configurado, se omiten métricas de Instagram: {exc}")

    if ig_id:
        for metric in IG_ACCOUNT_METRICS:
            value = fetch_metric(ig_id, metric, {"period": "day"})
            if value is not None:
                rows.append([today, "instagram", "account", "", metric, value])

    page_id = None
    try:
        page_id = fb_page_id()
    except MetaApiError as exc:
        print(f"FB_PAGE_ID no configurado, se omiten métricas de Facebook: {exc}")

    if page_id:
        for metric in FB_PAGE_METRICS:
            value = fetch_metric(page_id, metric, {"period": "day"})
            if value is not None:
                rows.append([today, "facebook", "account", "", metric, value])

    return rows


def collect_post_metrics(today, posted_entries):
    rows = []
    for entry in posted_entries:
        platform = entry["platform"]
        post_id = entry["platform_post_id"]
        metrics = IG_POST_METRICS if platform == "instagram" else FB_POST_METRICS
        for metric in metrics:
            value = fetch_metric(post_id, metric)
            if value is not None:
                rows.append([today, platform, "post", post_id, metric, value])
    return rows


def append_csv_rows(rows):
    file_exists = METRICS_CSV_PATH.exists()
    with open(METRICS_CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(CSV_HEADER)
        writer.writerows(rows)


def read_all_csv_rows():
    if not METRICS_CSV_PATH.exists():
        return []
    with open(METRICS_CSV_PATH, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def generate_report(posted_entries):
    all_rows = read_all_csv_rows()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    latest_account_rows = [r for r in all_rows if r["scope"] == "account" and r["date"] == today]

    lines = ["# Reporte de métricas", "", f"_Actualizado: {today} (UTC)_", ""]

    lines.append("## Resumen de cuentas (hoy)")
    if latest_account_rows:
        for platform in ("instagram", "facebook"):
            platform_rows = [r for r in latest_account_rows if r["platform"] == platform]
            if not platform_rows:
                continue
            lines.append(f"\n**{platform.capitalize()}**")
            for r in platform_rows:
                lines.append(f"- {r['metric_name']}: {r['value']}")
    else:
        lines.append("\n_Aún no hay datos de cuenta para hoy._")

    lines.append("\n## Últimos posts publicados")
    recent_posts = sorted(posted_entries, key=lambda e: e.get("posted_at") or "", reverse=True)[:5]
    if recent_posts:
        lines.append("\n| Fecha | Plataforma | Caption | Métricas |")
        lines.append("|---|---|---|---|")
        for entry in recent_posts:
            post_id = entry["platform_post_id"]
            post_rows = [r for r in all_rows if r["scope"] == "post" and r["post_id"] == post_id]
            metrics_str = ", ".join(f"{r['metric_name']}={r['value']}" for r in post_rows) or "_sin datos aún_"
            caption = (entry.get("caption") or "")[:40].replace("|", "/")
            posted_at = (entry.get("posted_at") or "")[:10]
            lines.append(f"| {posted_at} | {entry['platform']} | {caption} | {metrics_str} |")
    else:
        lines.append("\n_Todavía no hay publicaciones registradas._")

    lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def commit_and_push():
    subprocess.run(["git", "config", "user.name", "socialmedia2026-bot"], cwd=REPO_ROOT, check=True)
    subprocess.run(
        ["git", "config", "user.email", "actions@users.noreply.github.com"], cwd=REPO_ROOT, check=True
    )
    subprocess.run(["git", "add", str(METRICS_CSV_PATH), str(REPORT_PATH)], cwd=REPO_ROOT, check=True)

    status = subprocess.run(
        ["git", "status", "--porcelain", str(METRICS_CSV_PATH), str(REPORT_PATH)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if not status.stdout.strip():
        print("No hay cambios en las métricas/reporte, no se hace commit.")
        return

    subprocess.run(["git", "commit", "-m", "Update metrics report [skip ci]"], cwd=REPO_ROOT, check=True)

    push = subprocess.run(["git", "push"], cwd=REPO_ROOT)
    if push.returncode != 0:
        print("Push rechazado, intentando rebase y reintentar una vez...")
        subprocess.run(["git", "pull", "--rebase"], cwd=REPO_ROOT, check=True)
        subprocess.run(["git", "push"], cwd=REPO_ROOT, check=True)


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    posted_entries = load_posted_entries()

    rows = collect_account_metrics(today) + collect_post_metrics(today, posted_entries)
    if rows:
        append_csv_rows(rows)
        print(f"Se guardaron {len(rows)} métricas nuevas.")
    else:
        print("No se obtuvo ninguna métrica nueva (revisa los mensajes [omitida] arriba).")

    generate_report(posted_entries)
    print(f"Reporte regenerado en {REPORT_PATH}")
    commit_and_push()


if __name__ == "__main__":
    main()
