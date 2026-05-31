import requests
from config.constants import url, coc_email, coc_password
from service.key_manager import get_dynamic_api_key


class ApiClient:

    def __init__(self):
        self.session = requests.Session()
        if not coc_email or not coc_password:
            raise Exception("No se configuró credenciales de desarrollador.")
        token = get_dynamic_api_key(coc_email, coc_password)
        self.session.headers = {
            "Authorization": token
        }

    def _encode_tag(self, clan_tag: str) -> str:
        return "%23" + clan_tag.lstrip("#")

    def get_clan_info(self, clan_tag: str):
        response = self.session.get(url=url + "clans/" + self._encode_tag(clan_tag))
        if response.status_code == 200:
            return response.json()
        print(f"Error al obtener información del clan: {response.status_code} - {response.text}")
        return None

    def get_current_war(self, clan_tag: str):
        response = self.session.get(url=url + "clans/" + self._encode_tag(clan_tag) + "/currentwar")
        if response.status_code == 200:
            return response.json()
        print(f"Error al obtener la guerra actual: {response.status_code} - {response.text}")
        return None