import requests
from config.constants import url, clan_tag, coc_email, coc_password
from service.key_manager import get_dynamic_api_key


class ApiClient:

    def __init__(self):
        self.session = requests.Session()
        token = None
        if not token and coc_email and coc_password:
            token = get_dynamic_api_key(coc_email, coc_password)
        if not token:
            raise Exception("No se configuró API key ni credenciales de desarrollador.")
        self.session.headers = {
            "Authorization": token
        }

    def get_current_war(self):
        response = self.session.get(url=url + "clans/" + clan_tag + "/currentwar")
        if response.status_code == 200:
            return response.json()
        if response.status_code == 403:
            print(f"Acceso denegado (403). Verifica la API key y la IP permitida.")
            return None

        print(f"Error al obtener la guerra actual: {response.status_code} - {response.text}")
        return None
    
    def get_war_log(self):
        response = self.session.get(url=url + "clans/" + clan_tag + "/warlog?limit=5")
        if response.status_code == 200:
            return response.json().get("items", [])
        if response.status_code == 403:
            print(f"Acceso denegado (403). Verifica la API key y la IP permitida.")
            return None

        print(f"Error al obtener el registro de guerras: {response.status_code} - {response.text}")
        return None