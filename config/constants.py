import os

# Si COC_API_KEY está definida, se usa directamente (ejecución local).
# Si no, se generará dinámicamente en ApiService usando email/password.
coc_email = os.environ.get("COC_EMAIL", "")
coc_password = os.environ.get("COC_PASSWORD", "")

# CLAN_TAGS: lista separada por comas, e.g. "ABC123,DEF456"
clan_tags = [tag.strip() for tag in os.environ.get("CLAN_TAGS", "").split(",") if tag.strip()]

url = "https://api.clashofclans.com/v1/"

