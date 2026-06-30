# Gestor de redes sociales — Instagram + Facebook

Este proyecto publica y programa publicaciones en tu Instagram y tu Página de Facebook, y te
arma un reportecito de métricas todos los días — todo automático, sin que tengas que tener tu
computadora prendida ni saber programar. Lo único que vas a tocar en el día a día es un archivo
de texto (`data/scheduled_posts.json`) y la carpeta `media/`, ambos editables directamente desde
la página web de GitHub.

**Nota de privacidad importante:** este repositorio es **público**. Eso significa que cualquiera
con el enlace puede ver los textos de tus publicaciones, las imágenes/videos que subas, las
fechas programadas y tus métricas (alcance, interacciones, etc.). Tus contraseñas y tokens
**nunca** están aquí — esos van protegidos como "Secrets" de GitHub, que nadie puede leer. Como
de todas formas tus publicaciones se vuelven públicas al salir en Instagram/Facebook, esto no es
un riesgo nuevo, solo queremos que lo sepas.

---

## 1. Qué necesitas antes de empezar

- Una cuenta de Instagram tipo **Business o Creator** (no personal), vinculada a una **Página de
  Facebook** que administres.
- Una cuenta gratuita en [GitHub](https://github.com) (ya tienes el repositorio creado).
- Una cuenta gratuita en [Meta for Developers](https://developers.facebook.com).

---

## 2. Crear tu app gratuita en Meta y obtener tus 5 datos

1. Entra a [developers.facebook.com](https://developers.facebook.com) e inicia sesión con tu
   cuenta de Facebook.
2. **Mis apps → Crear app**. Elige el tipo **"Negocio"**. Ponle el nombre que quieras (ej. "Mis
   redes 2026").
3. Dentro de tu app, en el panel, agrega el producto **"Instagram"** (Instagram Platform) y
   asegúrate de tener acceso a la **API de Páginas de Facebook** (se agrega automáticamente con
   el tipo Negocio).
4. Anota tu **App ID** y tu **App Secret** (Configuración → Básica). Esto es `META_APP_ID` y
   `META_APP_SECRET`.
5. Ve a la herramienta **Graph API Explorer**
   (developers.facebook.com/tools/explorer):
   - Selecciona tu app en el menú superior.
   - Click en **"Generar token de acceso"** y marca estos permisos:
     `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`,
     `pages_read_user_content`, `instagram_basic`, `instagram_content_publish`,
     `instagram_manage_insights`, `business_management`.
   - Copia el token que te genera (es de corta duración, lo vamos a "alargar" en el paso
     siguiente).
6. Convierte ese token en uno de **larga duración**: pega esta URL en tu navegador,
   reemplazando los valores entre `<>`:
   ```
   https://graph.facebook.com/v23.0/oauth/access_token?grant_type=fb_exchange_token&client_id=<TU_APP_ID>&client_secret=<TU_APP_SECRET>&fb_exchange_token=<TU_TOKEN_CORTO>
   ```
   Te va a devolver un `access_token` nuevo, más largo — ese es tu token de usuario de larga
   duración.
7. Con ese token de usuario de larga duración, entra a esta URL (reemplazando el token):
   ```
   https://graph.facebook.com/v23.0/me/accounts?access_token=<TU_TOKEN_LARGO>
   ```
   Vas a ver una lista con tu(s) Página(s). Anota:
   - `id` → este es tu **`FB_PAGE_ID`**.
   - `access_token` (el que aparece dentro de esa Página, no el de arriba) → este es tu
     **`PAGE_ACCESS_TOKEN`**. Este token de Página, generado así, **no caduca**, aunque se puede
     invalidar si cambias tu contraseña, revocas permisos, o tu cuenta de Facebook está inactiva
     ~90 días. Por eso de vez en cuando conviene repetir este proceso (ver sección 7).
8. Para obtener tu **`IG_BUSINESS_ACCOUNT_ID`**, entra a esta URL (con tu Page ID y tu Page
   Access Token del paso anterior):
   ```
   https://graph.facebook.com/v23.0/<FB_PAGE_ID>?fields=instagram_business_account&access_token=<PAGE_ACCESS_TOKEN>
   ```
   El número que te devuelve dentro de `instagram_business_account` es tu
   `IG_BUSINESS_ACCOUNT_ID`.

Al terminar deberías tener anotados estos 5 valores:

| Nombre | De dónde sale |
|---|---|
| `META_APP_ID` | Configuración básica de tu app |
| `META_APP_SECRET` | Configuración básica de tu app |
| `PAGE_ACCESS_TOKEN` | Paso 7 |
| `FB_PAGE_ID` | Paso 7 |
| `IG_BUSINESS_ACCOUNT_ID` | Paso 8 |

---

## 3. Cargar esos 5 valores como Secrets en GitHub

1. En tu repositorio en GitHub, ve a **Settings → Secrets and variables → Actions**.
2. Click en **"New repository secret"**, una vez por cada uno de los 5 valores de arriba. El
   **nombre** debe ser exactamente igual al de la tabla (ej. `META_APP_ID`), y el **valor** es lo
   que anotaste.
3. Al terminar deberías ver los 5 secrets listados (GitHub nunca muestra el valor de nuevo, solo
   el nombre — guarda tus valores en otro lugar seguro por si los necesitas de nuevo).

---

## 4. Cómo programar una publicación (lo que harás día a día)

1. Sube tu imagen o video: en GitHub, entra a la carpeta `media/` → **"Add file" → "Upload
   files"** → arrastra tu archivo → **Commit changes**.
2. Abre `data/scheduled_posts.json` → click en el ícono de lápiz (✏️) para editarlo.
3. Copia un bloque de ejemplo de `data/scheduled_posts.example.json` y pégalo dentro de los
   corchetes `[ ]` del archivo `scheduled_posts.json` (si ya hay otras publicaciones, agrega una
   coma `,` después del último bloque existente y pega el nuevo).
4. Completa los campos:
   - `"id"`: cualquier texto único, ej. `"2026-07-05-001"`.
   - `"platform"`: `"instagram"` o `"facebook"`.
   - `"media_type"`: `"IMAGE"` para fotos (o `"VIDEO"`/`"REELS"` en Instagram para video).
   - `"media_path"`: la ruta exacta del archivo que subiste, ej. `"media/foto-verano.jpg"`
     (¡cuidado con mayúsculas/minúsculas, deben coincidir exacto!).
   - `"caption"`: el texto de tu publicación.
   - `"scheduled_datetime"`: fecha y hora **en UTC**, formato `AAAA-MM-DDTHH:MM:SSZ` (ej.
     `"2026-07-05T15:00:00Z"`). Si no sabes convertir tu hora local a UTC, busca "hora actual UTC"
     en internet y calcula la diferencia con tu hora.
   - Deja `"status": "scheduled"`, y `"posted_at"`, `"platform_post_id"`, `"error"` siempre como
     `null` — el sistema los completa solo.
5. **Commit directamente en `main`**.
6. Listo. El sistema revisa cada ~15 minutos si ya es hora de publicar algo.

> **Importante:** la hora de salida real puede variar entre 15 y 45 minutos respecto a lo que
> pusiste, porque así de preciso es el sistema de cron gratuito de GitHub. No uses esto para
> algo que necesite salir exactamente en un minuto puntual (ej. ligado a un evento en vivo).

> **Límite de Instagram:** no se pueden publicar más de 25 contenidos por cuenta en 24 horas.

---

## 5. Cómo verificar que funcionó

1. En tu repositorio, ve a la pestaña **Actions**.
2. Vas a ver las corridas de "Publicar posts programados" — un ✅ verde significa que corrió bien
   (aunque eso no garantiza que *tu* post específico haya salido, solo que el robot corrió sin
   errores generales). Para confirmar tu post puntual, revisa `data/scheduled_posts.json`: tu
   entrada debería tener `"status": "posted"` y un `"platform_post_id"`.
3. Si ves `"status": "failed"`, el campo `"error"` te va a decir, en el mensaje de Meta, qué
   salió mal (ver la sección de errores comunes abajo).
4. También puedes entrar a Actions → "Publicar posts programados" → **"Run workflow"** para
   forzar una corrida inmediata sin esperar al próximo ciclo de 15 minutos.

---

## 6. Cómo funcionan los reportes de métricas

Todos los días a las 8:00 UTC (puedes forzarlo manualmente desde Actions → "Reporte diario de
métricas" → "Run workflow"), el sistema consulta tus números reales en Meta y actualiza
`reports/REPORT.md` — ábrelo directamente en GitHub, se ve formateado como una página normal.
Ahí vas a ver un resumen de tu cuenta y una tabla con tus últimos posts y sus métricas. No
necesitas abrir `data/metrics_history.csv` (es el detalle técnico que respalda el reporte).

---

## 7. Renovar tu token de acceso (cada ~2 meses, como buen hábito)

El `PAGE_ACCESS_TOKEN` generado siguiendo la sección 2 no tiene fecha de caducidad fija, pero
Meta puede invalidarlo si cambias tu contraseña, revocas permisos, o tu cuenta está inactiva
mucho tiempo. Como hábito de seguridad, cada 60-90 días repite los **pasos 5 a 7 de la sección
2** para generar un token fresco, y actualiza el secret `PAGE_ACCESS_TOKEN` en GitHub (Settings →
Secrets and variables → Actions → click en `PAGE_ACCESS_TOKEN` → **"Update secret"**). Te
recomendamos poner un recordatorio en tu calendario.

---

## 8. Preguntas frecuentes / errores comunes

| Mensaje de error | Qué significa | Qué hacer |
|---|---|---|
| `media download failed` / contenedor no llega a `FINISHED` | Instagram no pudo descargar tu imagen/video | Revisa que el nombre en `media_path` coincida exacto (mayúsculas incluidas) con el archivo en `media/`. Si acabas de subir la imagen en el mismo commit, espera ~10 minutos a que se propague antes de que el sistema reintente. |
| `Invalid OAuth access token` | Tu token venció o se invalidó | Repite la sección 7 para generar uno nuevo. |
| `(#10) ... permission` | Falta algún permiso al generar el token | Repite la sección 2 paso 5 y marca todos los permisos listados. |
| Falta una variable de entorno (`META_APP_ID`, etc.) | Un secret no está bien cargado en GitHub | Revisa la sección 3, que el nombre del secret sea exactamente igual. |

Si algo falla de forma rara, entra a **Actions** → click en la corrida en rojo → click en el paso
que falló para ver el mensaje completo de Meta.

---

## 9. ¿Cómo sé que todo quedó bien configurado?

Antes de programar tu primera publicación real:

1. Ve a **Actions → "Verificar credenciales" → Run workflow**. Si todo está bien, vas a ver en el
   log el nombre real de tu Página de Facebook y tu usuario de Instagram.
2. Haz una prueba real: agrega una entrada en `scheduled_posts.json` con fecha unos minutos en el
   pasado, dispara manualmente "Publicar posts programados", y confirma que el post aparece en tu
   cuenta real.

---

## Estructura del proyecto (referencia técnica, no necesitas tocar esto)

```
scripts/meta_api.py        - cliente de la API de Meta
scripts/publish.py         - lógica de publicación en IG/FB
scripts/check_scheduled.py - revisa y publica lo que esté programado (corre cada 15 min)
scripts/fetch_metrics.py   - trae métricas y regenera el reporte (corre 1 vez al día)
scripts/check_credentials.py - verifica que los 5 secrets estén bien (manual)
.github/workflows/         - la configuración de los robots automáticos de GitHub
```
