"""Verifica que los 5 secrets estén bien configurados, mostrando el nombre real de tu
Página de Facebook y tu usuario de Instagram. Pensado para correr una sola vez, manualmente,
desde la pestaña Actions, antes de programar la primera publicación de verdad."""

from meta_api import MetaApiError, fb_page_id, graph_get, ig_business_account_id


def main():
    print("Verificando credenciales de Meta...\n")

    try:
        page = graph_get(fb_page_id(), {"fields": "name"})
        print(f"Página de Facebook detectada: {page.get('name')!r}")
    except MetaApiError as exc:
        print(f"ERROR al verificar la Página de Facebook: {exc}")

    try:
        ig = graph_get(ig_business_account_id(), {"fields": "username"})
        print(f"Cuenta de Instagram detectada: @{ig.get('username')}")
    except MetaApiError as exc:
        print(f"ERROR al verificar la cuenta de Instagram: {exc}")

    print("\nSi ambos nombres de arriba son los tuyos, las credenciales están bien configuradas.")


if __name__ == "__main__":
    main()
