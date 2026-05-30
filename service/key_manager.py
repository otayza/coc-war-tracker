import requests


DEV_API_URL = "https://developer.clashofclans.com/api"


def get_current_ip():
    """Obtiene la IP pública actual."""
    response = requests.get("https://api.ipify.org")
    response.raise_for_status()
    return response.text.strip()


def get_dynamic_api_key(email: str, password: str) -> str:
    """
    Genera una API key de Clash of Clans válida para la IP actual.
    Usa el portal de desarrolladores para login y gestión de keys.
    """
    session = requests.Session()

    # 1. Login
    resp = session.post(f"{DEV_API_URL}/login", json={
        "email": email,
        "password": password
    })
    if resp.status_code != 200:
        raise Exception(f"Login fallido: {resp.status_code} - {resp.text}")

    # 2. Obtener IP actual
    current_ip = get_current_ip()
    print(f"IP actual: {current_ip}")

    # 3. Listar keys existentes
    resp = session.post(f"{DEV_API_URL}/apikey/list")
    if resp.status_code != 200:
        raise Exception(f"Error listando keys: {resp.status_code}")

    keys = resp.json().get("keys", [])

    # 4. Buscar si ya hay una key para esta IP
    for key in keys:
        cidrs = key.get("cidrRanges", [])
        if current_ip in cidrs:
            print("Key existente encontrada para esta IP.")
            return f"Bearer {key['key']}"

    # 5. Si hay más de 1 key borrar la más antigua
    if len(keys) > 1:
        oldest_key = keys[0]
        resp = session.post(f"{DEV_API_URL}/apikey/revoke", json={
            "id": oldest_key["id"]
        })
        if resp.status_code != 200:
            raise Exception(f"Error revocando key: {resp.status_code}")
        print(f"Key antigua revocada: {oldest_key['id']}")

    # 6. Crear nueva key para la IP actual
    resp = session.post(f"{DEV_API_URL}/apikey/create", json={
        "name": f"github-actions-{current_ip}",
        "description": "Auto-generated key for GitHub Actions",
        "cidrRanges": [current_ip],
        "scopes": ["clash"]
    })
    if resp.status_code != 200:
        raise Exception(f"Error creando key: {resp.status_code} - {resp.text}")

    new_key = resp.json()["key"]["key"]
    print("Nueva API key creada correctamente.")
    return f"Bearer {new_key}"
