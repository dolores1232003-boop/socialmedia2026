"""Cliente delgado para la Graph API de Meta (Facebook + Instagram)."""

import os
import requests

GRAPH_API_VERSION = "v23.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# jsDelivr sirve archivos de un repo público de GitHub con el Content-Type correcto
# (raw.githubusercontent.com sirve text/plain y causa fallos intermitentes al publicar en IG).
JSDELIVR_BASE = "https://cdn.jsdelivr.net/gh/{owner}/{repo}@{branch}"


class MetaApiError(Exception):
    """Error devuelto por la Graph API de Meta, con el mensaje original de Meta."""


def _credential(name):
    value = os.environ.get(name)
    if not value:
        raise MetaApiError(
            f"Falta la variable de entorno {name}. Revisa que el secret esté "
            f"configurado en GitHub Actions (Settings > Secrets and variables > Actions)."
        )
    return value


def page_access_token():
    return _credential("PAGE_ACCESS_TOKEN")


def fb_page_id():
    return _credential("FB_PAGE_ID")


def ig_business_account_id():
    return _credential("IG_BUSINESS_ACCOUNT_ID")


def _raise_for_meta_error(response):
    try:
        body = response.json()
    except ValueError:
        response.raise_for_status()
        return
    if "error" in body:
        err = body["error"]
        message = err.get("message", "Error desconocido de Meta")
        subcode = err.get("error_subcode")
        code = err.get("code")
        detail = f"[code={code} subcode={subcode}] {message}"
        raise MetaApiError(detail)
    response.raise_for_status()


def graph_get(path, params=None):
    params = dict(params or {})
    params.setdefault("access_token", page_access_token())
    response = requests.get(f"{GRAPH_API_BASE}/{path}", params=params, timeout=30)
    _raise_for_meta_error(response)
    return response.json()


def graph_post(path, data=None):
    data = dict(data or {})
    data.setdefault("access_token", page_access_token())
    response = requests.post(f"{GRAPH_API_BASE}/{path}", data=data, timeout=60)
    _raise_for_meta_error(response)
    return response.json()


def build_media_url(media_path, owner=None, repo=None, branch="main"):
    """Convierte una ruta relativa del repo (ej. 'media/foto.jpg') en una URL pública.

    owner/repo se leen de GITHUB_REPOSITORY (formato "owner/repo") si no se pasan
    explícitamente; esa variable la define GitHub Actions automáticamente.
    """
    if owner is None or repo is None:
        gh_repo = os.environ.get("GITHUB_REPOSITORY")
        if not gh_repo or "/" not in gh_repo:
            raise MetaApiError(
                "No se pudo determinar owner/repo para construir la URL de la imagen. "
                "Define GITHUB_REPOSITORY o pasa owner/repo explícitamente."
            )
        owner, repo = gh_repo.split("/", 1)
    base = JSDELIVR_BASE.format(owner=owner, repo=repo, branch=branch)
    return f"{base}/{media_path.lstrip('/')}"
