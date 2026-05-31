import os
from datetime import datetime
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader

from service.ApiService import ApiClient
from config.constants import clan_tags
from db.database import Database


def process_war(db: Database, client: ApiClient, clan_tag: str):
    """Consulta la guerra actual de un clan y guarda participaciones."""
    war = client.get_current_war(clan_tag)

    if not war:
        print(f"[{clan_tag}] No se pudo obtener información de guerra.")
        return False

    clan_name = war.get('clan', {}).get('name', clan_tag)
    state = war.get("state")
    print(f"[{clan_name}] Estado de la guerra: {state}")

    if state not in ("inWar", "warEnded"):
        print(f"[{clan_name}] La guerra está en preparación. No hay ataques todavía.")
        return False

    war_end_time = war.get("endTime")

    members = war.get("clan", {}).get("members", [])
    current_attacks = sum(len(m.get("attacks", [])) for m in members)

    prev_attacks = db.get_war_attack_count(clan_tag, war_end_time)
    if current_attacks == prev_attacks:
        print(f"[{clan_name}] Sin ataques nuevos ({current_attacks} ataques).")
        return False

    for member in members:
        attacks = member.get("attacks", [])
        stars = sum(a.get("stars", 0) for a in attacks)
        db.upsert_participation(
            clan_tag=clan_tag,
            player_tag=member.get("tag"),
            player_name=member.get("name"),
            townhall_level=member.get("townhallLevel", 0),
            stars=stars,
            attacks=len(attacks),
            war_end_time=war_end_time
        )

    db.update_war_attack_count(clan_tag, war_end_time, current_attacks)
    print(f"[{clan_name}] Actualizados {len(members)} jugadores de la guerra ({state}, {war_end_time}). Ataques: {current_attacks}.")
    return True


def generate_html(db: Database, clan_info: dict, clan_tag: str):
    """Genera el HTML estático con las estadísticas de un clan."""
    players = db.get_player_stats(clan_tag)
    recent_wars = db.get_recent_wars(clan_tag)

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    output_dir = os.path.join(os.path.dirname(__file__), "docs", clan_info.get("name", "").lstrip("#").replace(" ", "_"))
    os.makedirs(output_dir, exist_ok=True)

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("index.html")

    html = template.render(
        players=players,
        recent_wars=recent_wars,
        clan_info=clan_info,
        updated_at=datetime.now(ZoneInfo("Europe/Madrid")).strftime("%d-%m-%y %H:%M")
    )

    output_path = os.path.join(output_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[{clan_info.get('name')}] HTML generado en {output_path}")


def generate_index(clans_info: list):
    """Genera el HTML índice con links a cada clan."""
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    output_dir = os.path.join(os.path.dirname(__file__), "docs")
    os.makedirs(output_dir, exist_ok=True)

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("home.html")

    clans = [
        {
            "name": info.get("name", ""),
            "tag": info.get("tag", ""),
            "folder": info.get("name", "").lstrip("#").replace(" ", "_")
        }
        for info in clans_info
    ]

    html = template.render(clans=clans)

    output_path = os.path.join(output_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Índice generado en {output_path}")


def main():
    db = Database()
    client = ApiClient()

    try:
        
        clans_info = []
        for clan_tag in clan_tags:
            clan_info = client.get_clan_info(clan_tag)
            members_changed = False
            if clan_info:
                clans_info.append(clan_info)
                clan_name = clan_info.get("name", clan_tag)
                members_changed = db.sync_clan_members(clan_tag, clan_info.get("memberList", []))
                if members_changed:
                    print(f"[{clan_name}] Miembros actualizados.")
                else:
                    print(f"[{clan_name}] Sin cambios en miembros.")
            has_updates = process_war(db, client, clan_tag)
            if has_updates or members_changed:
                generate_html(db, clan_info, clan_tag)
                generate_index(clans_info)

        db.purge_old_records(max_wars=15)
    finally:
        db.close()


if __name__ == "__main__":
    main()
