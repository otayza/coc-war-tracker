# CoC War Tracker

Seguimiento automático de estadísticas de guerra de Clash of Clans. Genera páginas HTML estáticas con rankings por clan, desplegadas con GitHub Pages.

## Funcionalidades

- Consulta la API de Clash of Clans para obtener datos de guerras en curso
- Almacena participaciones (estrellas, ataques, TH) en SQLite
- Soporta múltiples clanes simultáneamente
- Genera HTML estático por clan con tabla ordenable (TH, estrellas, promedio)
- Solo actualiza si hay ataques nuevos o cambios en miembros
- Purga automática de guerras antiguas (mantiene las últimas 15)

## Configuración

Variables de entorno (`.env` o GitHub Secrets/Variables):

```
COC_EMAIL=tu@email.com
COC_PASSWORD=tu_password
CLAN_TAGS=TAG1,TAG2
```

## Uso local

```bash
pip install -r requirements.txt
python main.py
```

## GitHub Actions

El workflow `.github/workflows/update-war-stats.yml` se ejecuta manualmente y:

1. Genera una API key dinámica para la IP del runner
2. Consulta guerras y actualiza la DB
3. Genera HTML en `docs/<NombreClan>/`
4. Commitea y pushea los cambios

## GitHub Pages

Configurar en Settings → Pages → Deploy from branch → `main` → `/docs`
