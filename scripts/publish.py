"""Funciones de publicación en Instagram y Facebook. Sin conocimiento del archivo JSON."""

import time

from meta_api import (
    MetaApiError,
    fb_page_id,
    graph_get,
    graph_post,
    ig_business_account_id,
)

IG_CONTAINER_POLL_INTERVAL_SECONDS = 5
IG_CONTAINER_MAX_POLLS = 24  # ~2 minutos de espera máxima


def publish_instagram_post(caption, media_url, media_type="IMAGE"):
    """Publica un post en Instagram vía el flujo de contenedor de 3 pasos.

    Devuelve el id del media publicado. Lanza MetaApiError con el mensaje de Meta
    si el contenedor termina en ERROR o si la API falla en cualquier paso.
    """
    ig_id = ig_business_account_id()

    container_params = {"caption": caption}
    if media_type == "REELS":
        container_params["media_type"] = "REELS"
        container_params["video_url"] = media_url
    elif media_type == "VIDEO":
        container_params["media_type"] = "VIDEO"
        container_params["video_url"] = media_url
    else:
        container_params["image_url"] = media_url

    container = graph_post(f"{ig_id}/media", container_params)
    creation_id = container.get("id")
    if not creation_id:
        raise MetaApiError(f"Meta no devolvió un creation_id al crear el contenedor: {container}")

    status_code = _wait_for_container_ready(creation_id)
    if status_code != "FINISHED":
        raise MetaApiError(
            f"El contenedor de Instagram no terminó en FINISHED (status={status_code}). "
            "Revisa que la URL de la imagen/video sea pública y válida."
        )

    publish_result = graph_post(f"{ig_id}/media_publish", {"creation_id": creation_id})
    published_id = publish_result.get("id")
    if not published_id:
        raise MetaApiError(f"Meta no devolvió un id al publicar: {publish_result}")
    return published_id


def _wait_for_container_ready(creation_id):
    for _ in range(IG_CONTAINER_MAX_POLLS):
        status = graph_get(creation_id, {"fields": "status_code"})
        status_code = status.get("status_code")
        if status_code in ("FINISHED", "ERROR"):
            return status_code
        time.sleep(IG_CONTAINER_POLL_INTERVAL_SECONDS)
    raise MetaApiError(
        "Tiempo de espera agotado esperando a que Instagram procese el contenedor de medios."
    )


def publish_facebook_post(message, media_url=None):
    """Publica un post inmediato en la Página de Facebook. Devuelve el id del post."""
    page_id = fb_page_id()
    if media_url:
        result = graph_post(f"{page_id}/photos", {"url": media_url, "caption": message})
        return result.get("post_id") or result.get("id")
    else:
        result = graph_post(f"{page_id}/feed", {"message": message})
        return result.get("id")
