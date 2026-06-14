#!/usr/bin/env python3
"""
WM-Tippspiel 2026 – Fetch live results from football-data.org and write data.json.

Requires: pip install requests
Env var:  FOOTBALL_API_KEY  (free at https://www.football-data.org/client/register)
"""

import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

import requests

API_KEY = os.environ.get("FOOTBALL_API_KEY", "")
BASE_URL = "https://api.football-data.org/v4"
COMPETITION = "WC"
SEASON = 2026

HEADERS = {"X-Auth-Token": API_KEY}

# Map API English names → German display names
TEAM_DE = {
    "Germany": "Deutschland", "France": "Frankreich", "Spain": "Spanien",
    "England": "England", "Argentina": "Argentinien", "Brazil": "Brasilien",
    "Netherlands": "Niederlande", "Portugal": "Portugal", "Switzerland": "Schweiz",
    "Morocco": "Marokko", "Paraguay": "Paraguay", "Uruguay": "Uruguay",
    "Croatia": "Kroatien", "Haiti": "Haiti", "Jordan": "Jordanien",
    "Saudi Arabia": "Saudi-Arabien", "Panama": "Panama",
    "Cabo Verde": "Kap Verde", "Cape Verde": "Kap Verde",
    "New Zealand": "Neuseeland", "Curaçao": "Curaçao", "Curacao": "Curaçao",
    "Mexico": "Mexiko", "South Korea": "Südkorea", "Korea Republic": "Südkorea",
    "Czech Republic": "Tschechien", "Czechia": "Tschechien",
    "Canada": "Kanada", "Bosnia and Herzegovina": "Bosnien-Hz.",
    "United States": "USA", "United States of America": "USA", "USA": "USA",
    "Qatar": "Katar", "South Africa": "Südafrika", "Scotland": "Schottland",
    "Ivory Coast": "Elfenbeinküste", "Côte d'Ivoire": "Elfenbeinküste",
    "Ecuador": "Ecuador", "Australia": "Australien",
    "Turkey": "Türkei", "Türkiye": "Türkei",
    "Japan": "Japan", "Senegal": "Senegal", "Nigeria": "Nigeria",
    "Cameroon": "Kamerun", "Colombia": "Kolumbien", "Chile": "Chile",
    "Venezuela": "Venezuela", "Bolivia": "Bolivien", "Costa Rica": "Costa Rica",
    "Honduras": "Honduras", "Jamaica": "Jamaika", "Iran": "Iran",
    "Serbia": "Serbien", "Ukraine": "Ukraine", "Poland": "Polen",
    "Belgium": "Belgien", "Romania": "Rumänien", "Austria": "Österreich",
    "Slovakia": "Slowakei", "Denmark": "Dänemark", "Sweden": "Schweden",
    "Norway": "Norwegen", "Albania": "Albanien", "Indonesia": "Indonesien",
    "China PR": "China",
}

GROUP_MAP = {
    "GROUP_A": "A", "GROUP_B": "B", "GROUP_C": "C", "GROUP_D": "D",
    "GROUP_E": "E", "GROUP_F": "F", "GROUP_G": "G", "GROUP_H": "H",
    "GROUP_I": "I", "GROUP_J": "J", "GROUP_K": "K", "GROUP_L": "L",
}

STAGE_DE = {
    "ROUND_OF_32": "Runde der 32",
    "ROUND_OF_16": "Achtelfinale",
    "QUARTER_FINALS": "Viertelfinale",
    "SEMI_FINALS": "Halbfinale",
    "THIRD_PLACE": "Spiel um Platz 3",
    "FINAL": "Finale",
}

# ── Player tips (hardcoded from the tipping PDF) ──────────────────────────────

PLAYER_TIPS = {
    "FlorianH": {
        "name": "Florian H.",
        "weltmeister": "Frankreich",
        "halbfinalisten": ["Spanien", "Frankreich", "Argentinien", "England"],
        "gelbeKarten": "Paraguay",
        "toreDeutschland": 7,
        "gegentore": "Haiti",
    },
    "FlorianP": {
        "name": "Florian P.",
        "weltmeister": "Spanien",
        "halbfinalisten": ["Spanien", "Frankreich", "Schweiz", "Portugal"],
        "gelbeKarten": "Portugal",
        "toreDeutschland": 7,
        "gegentore": "Jordanien",
    },
    "Manuel": {
        "name": "Manuel",
        "weltmeister": "Deutschland",
        "halbfinalisten": ["Deutschland", "Spanien", "Argentinien", "Brasilien"],
        "gelbeKarten": "Marokko",
        "toreDeutschland": 6,
        "gegentore": "Saudi-Arabien",
    },
    "Benjamin": {
        "name": "Benjamin",
        "weltmeister": "Spanien",
        "halbfinalisten": ["Frankreich", "Spanien", "Brasilien", "Niederlande"],
        "gelbeKarten": "Uruguay",
        "toreDeutschland": 6,
        "gegentore": "Panama",
    },
    "Christian": {
        "name": "Christian",
        "weltmeister": "Spanien",
        "halbfinalisten": ["England", "Spanien", "Argentinien", "Deutschland"],
        "gelbeKarten": "Argentinien",
        "toreDeutschland": 7,
        "gegentore": "Kap Verde",
    },
    "Thaddaeus": {
        "name": "Thaddäus",
        "weltmeister": "England",
        "halbfinalisten": ["England", "Portugal", "Spanien", "Deutschland"],
        "gelbeKarten": "Argentinien",
        "toreDeutschland": 6,
        "gegentore": "Kap Verde",
    },
    "Sebastian": {
        "name": "Sebastian",
        "weltmeister": "Frankreich",
        "halbfinalisten": ["Deutschland", "Frankreich", "Brasilien", "Spanien"],
        "gelbeKarten": "Marokko",
        "toreDeutschland": 7,
        "gegentore": "Neuseeland",
    },
    "Peter": {
        "name": "Peter",
        "weltmeister": "Spanien",
        "halbfinalisten": ["Spanien", "Frankreich", "Brasilien", "Deutschland"],
        "gelbeKarten": "Kroatien",
        "toreDeutschland": 7,
        "gegentore": "Haiti",
    },
    "Thassilo": {
        "name": "Thassilo",
        "weltmeister": "Frankreich",
        "halbfinalisten": ["Spanien", "Frankreich", "Brasilien", "Argentinien"],
        "gelbeKarten": "Argentinien",
        "toreDeutschland": 6,
        "gegentore": "Curaçao",
    },
    "David": {
        "name": "David",
        "weltmeister": "Spanien",
        "halbfinalisten": ["Frankreich", "Spanien", "England", "Argentinien"],
        "gelbeKarten": "Argentinien",
        "toreDeutschland": 8,
        "gegentore": "Haiti",
    },
    "Max": {
        "name": "Max",
        "weltmeister": "Spanien",
        "halbfinalisten": ["Spanien", "Frankreich", "Brasilien", "Argentinien"],
        "gelbeKarten": "Argentinien",
        "toreDeutschland": 7,
        "gegentore": "Kap Verde",
    },
}

PLAYER_ORDER = [
    "FlorianH", "FlorianP", "Manuel", "Benjamin", "Christian",
    "Thaddaeus", "Sebastian", "Peter", "Thassilo", "David", "Max",
]


# ── API helpers ───────────────────────────────────────────────────────────────

def api_get(path, params=None):
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, headers=HEADERS, params=params, timeout=20)
    if resp.status_code == 429:
        print("  Rate limited, waiting 65s …")
        time.sleep(65)
        resp = requests.get(url, headers=HEADERS, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def de(name):
    return TEAM_DE.get(name, name)


# ── Data fetching ─────────────────────────────────────────────────────────────

def fetch_all_matches():
    data = api_get(f"/competitions/{COMPETITION}/matches", {"season": SEASON})
    return data.get("matches", [])


def fetch_bookings(match_id):
    try:
        data = api_get(f"/matches/{match_id}")
        return (data.get("match") or data).get("bookings", [])
    except Exception as e:
        print(f"  Warning: could not fetch bookings for match {match_id}: {e}")
        return []


def format_match(m):
    stage = m.get("stage", "")
    group_raw = m.get("group") or ""
    ft = m.get("score", {}).get("fullTime", {})
    return {
        "id": m.get("id"),
        "date": (m.get("utcDate") or "")[:10],
        "utcDate": m.get("utcDate", ""),
        "group": GROUP_MAP.get(group_raw) or STAGE_DE.get(stage) or stage,
        "homeTeam": de(m.get("homeTeam", {}).get("name", "")),
        "awayTeam": de(m.get("awayTeam", {}).get("name", "")),
        "homeGoals": ft.get("home"),
        "awayGoals": ft.get("away"),
        "status": m.get("status", ""),
        "stage": stage,
    }


# ── Statistics ────────────────────────────────────────────────────────────────

def aggregate(matches):
    germany_goals = 0
    germany_games = 0
    goals_against: dict = defaultdict(int)
    yellow_cards: dict = defaultdict(int)
    finished_group_ids = []
    semifinalists = []
    world_champion = None

    for m in matches:
        status = m.get("status", "")
        stage = m.get("stage", "")
        ft = m.get("score", {}).get("fullTime", {})
        hg = ft.get("home")
        ag = ft.get("away")
        home = de(m.get("homeTeam", {}).get("name", ""))
        away = de(m.get("awayTeam", {}).get("name", ""))

        if status != "FINISHED":
            continue

        # Goals conceded
        if hg is not None and ag is not None:
            goals_against[home] += ag
            goals_against[away] += hg

        # Germany group stage goals
        if stage == "GROUP_STAGE":
            if home == "Deutschland":
                germany_goals += hg or 0
                germany_games += 1
            elif away == "Deutschland":
                germany_goals += ag or 0
                germany_games += 1
            finished_group_ids.append(m.get("id"))

        # Semifinalists
        if stage == "SEMI_FINALS" and hg is not None and ag is not None:
            if hg > ag:
                semifinalists.append(home)
            elif ag > hg:
                semifinalists.append(away)

        # World champion
        if stage == "FINAL" and hg is not None and ag is not None:
            if hg > ag:
                world_champion = home
            elif ag > hg:
                world_champion = away

    # Yellow cards – one API call per finished group match
    print(f"  Fetching yellow cards for {len(finished_group_ids)} group stage matches …")
    for i, mid in enumerate(finished_group_ids):
        if i > 0 and i % 9 == 0:
            print("  Pausing for rate limit …")
            time.sleep(65)
        for booking in fetch_bookings(mid):
            if booking.get("type") == "YELLOW_CARD":
                team_name = booking.get("team", {}).get("name", "")
                yellow_cards[de(team_name)] += 1

    top_yellow = max(yellow_cards, key=yellow_cards.get) if yellow_cards else None
    top_conceded = max(goals_against, key=goals_against.get) if goals_against else None

    return {
        "germanyGoals": germany_goals,
        "germanyGames": germany_games,
        "yellowCardsByTeam": dict(sorted(yellow_cards.items(), key=lambda x: -x[1])),
        "goalsAgainstByTeam": dict(sorted(goals_against.items(), key=lambda x: -x[1])),
        "topYellowCardTeam": top_yellow,
        "topGoalsAgainstTeam": top_conceded,
        "semifinals": list(set(semifinalists)),
        "worldChampion": world_champion,
    }


# ── Points calculation ────────────────────────────────────────────────────────

def calc_scores(stats):
    world_champion = stats["worldChampion"]
    actual_sf = set(stats["semifinals"])
    top_yellow = stats["topYellowCardTeam"]
    de_goals = stats["germanyGoals"]
    de_games = stats["germanyGames"]
    top_conceded = stats["topGoalsAgainstTeam"]

    # These questions are only scoreable once the relevant phase is complete
    vr_done = de_games >= 3
    sf_done = len(actual_sf) >= 4
    tournament_done = bool(world_champion)

    scores = {}
    for key in PLAYER_ORDER:
        t = PLAYER_TIPS[key]
        s = {
            "weltmeister": None,       # None = not yet decided
            "halbfinalisten": None,
            "gelbeKarten": None,
            "toreDeutschland": None,
            "gegentore": None,
            "total": 0,
        }

        # Weltmeister (5 pts) – decided when Final is played
        if tournament_done:
            pts = 5 if t["weltmeister"] == world_champion else 0
            s["weltmeister"] = pts
            s["total"] += pts

        # Halbfinalisten (1 pt each, +5 bonus if all 4 correct)
        if sf_done:
            tipped = set(t["halbfinalisten"])
            correct = len(tipped & actual_sf)
            pts = 5 if correct == 4 else correct
            s["halbfinalisten"] = pts
            s["total"] += pts
        elif actual_sf:
            # Show provisional partial count for confirmed SF teams
            tipped = set(t["halbfinalisten"])
            s["halbfinalisten"] = len(tipped & actual_sf)  # provisional
            s["total"] += s["halbfinalisten"]

        # Gelbe Karten (3 pts) – only meaningful at end of tournament
        if tournament_done and top_yellow:
            pts = 3 if t["gelbeKarten"] == top_yellow else 0
            s["gelbeKarten"] = pts
            s["total"] += pts

        # Tore Deutschland (3 pts, ±1) – after all 3 group games
        if vr_done:
            pts = 3 if abs(t["toreDeutschland"] - de_goals) <= 1 else 0
            s["toreDeutschland"] = pts
            s["total"] += pts

        # Gegentore (3 pts) – only after tournament ends
        if tournament_done and top_conceded:
            pts = 3 if t["gegentore"] == top_conceded else 0
            s["gegentore"] = pts
            s["total"] += pts

        scores[key] = s
    return scores


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not API_KEY:
        print("ERROR: FOOTBALL_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    print("Fetching WM 2026 matches …")
    raw_matches = fetch_all_matches()
    print(f"  → {len(raw_matches)} total matches")

    matches_json = [format_match(m) for m in raw_matches]
    stats = aggregate(raw_matches)

    print(f"  Germany: {stats['germanyGoals']} goals in {stats['germanyGames']} games")
    print(f"  Top yellow: {stats['topYellowCardTeam']}")
    print(f"  Top conceded: {stats['topGoalsAgainstTeam']}")
    print(f"  Semifinalists: {stats['semifinals']}")
    print(f"  World champion: {stats['worldChampion']}")

    scores = calc_scores(stats)

    output = {
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "playerOrder": PLAYER_ORDER,
        "playerTips": PLAYER_TIPS,
        "matches": matches_json,
        **stats,
        "scores": scores,
    }

    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Written {out_path}")


if __name__ == "__main__":
    main()
