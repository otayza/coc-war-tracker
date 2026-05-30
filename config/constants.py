import os

# Si COC_API_KEY está definida, se usa directamente (ejecución local).
# Si no, se generará dinámicamente en ApiService usando email/password.
coc_email = os.environ.get("COC_EMAIL", "")
coc_password = os.environ.get("COC_PASSWORD", "")
clan_tag = "%23"+os.environ.get("CLAN_TAGS", "")  

url = "https://api.clashofclans.com/v1/"

