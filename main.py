import os 
import csv
import random
import requests
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(title="Football AI Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAPIDAPI_KEY = "2ac6bb003amshea4487405e15e1fp18b95ejsn700b80898b4a"

# ==============================================================================
# LISTA DE LIGI PERMISE (WHITELIST)
# ==============================================================================
ALLOWED_LEAGUES = [
    "premier league", "la liga", "serie a", "bundesliga", "ligue 1",
    "championship", "2. bundesliga", "serie b", "segunda division",
    "eredivisie", "liga portugal", "pro league", "super lig", "premiership",
    "superliga", "liga 1", "liga i",
    "champions league", "europa league", "conference league", "nations league",
    "brasileiro", "serie a brazil", "copa libertadores", "copa sudamericana", "mls"
]

# ==============================================================================
# 1. FUNCTIA DE MEMORIE & ÎNVĂȚARE
# ==============================================================================
def load_league_confidence_thresholds():
    file_path = "istoric_invatare.csv"
    if not os.path.exists(file_path):
        return {}

    stats_per_league = {}

    try:
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                liga = row.get("liga", "").strip()
                status = row.get("status", "").strip()
                
                if not liga:
                    continue
                
                if liga not in stats_per_league:
                    stats_per_league[liga] = {"total": 0, "wins": 0}
                
                stats_per_league[liga]["total"] += 1
                if status == "WIN":
                    stats_per_league[liga]["wins"] += 1

        league_accuracy = {}
        for liga, data in stats_per_league.items():
            if data["total"] > 0:
                league_accuracy[liga] = round((data["wins"] / data["total"]) * 100, 2)

        return league_accuracy
    except Exception as e:
        print(f"--> Eroare la citirea fișierului istoric_invatare.csv: {e}")
        return {}

# ==============================================================================
# 2. MOTORUL DE DECIZIE AI
# ==============================================================================
def calculate_ai_prediction(p_15, p_25, p_gg, p_ht, p_st): 
    """
    Motor de decizie bazat exclusiv pe indicatori statistici
    (fără dependență de cote).
    """
    # 1. Pronosticuri pe Goluri / Ambele Marchează
    if p_25 >= 70.0 and p_gg >= 60.0:
        return "Peste 2.5 Goluri"
    if p_gg >= 68.0:
        return "GG (Ambele marchează)"
    if p_15 >= 78.0:
        return "Peste 1.5 Goluri"

    # 2. Pronosticuri pe Rezultat Final / Pauză (bazat pe dominantă statistică)
    if p_ht >= 75.0 and p_st >= 65.0:
        return "1 (Dominare Gazde)"
    elif p_ht <= 40.0 and p_st <= 45.0:
        return "2 (Dominare Oaspeți)"
    elif p_ht >= 60.0:
        return "1X"
    
    return "X2"

# ==============================================================================
# 3. SALVARE AUTOMATĂ MECIURI (SUPRASCRIERE PENTRU ZIUA CURENTĂ)
# ==============================================================================
def save_matches_to_csv(matches):
    file_path = "meciuri_azi.csv"
    today_str = datetime.now().strftime("%Y%m%d")

    try:
        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            fieldnames = ["data", "liga", "echipa_gazda", "echipa_oaspete", "pronostic", "cota", "status"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for m in matches:
                pred = m['prediction']
                if pred == "1":
                    cota = m['odds1']
                elif pred == "2":
                    cota = m['odds2']
                else:
                    cota = m['oddsX']

                writer.writerow({
                    "data": today_str,
                    "liga": m['league'],
                    "echipa_gazda": m['homeTeam'],
                    "echipa_oaspete": m['awayTeam'],
                    "pronostic": pred,
                    "cota": cota,
                    "status": "PENDING"
                })

        print(f"--> [AUTO-SAVE] S-au salvat {len(matches)} meciuri noi în '{file_path}'.")
    except Exception as e:
        print(f"--> Eroare la salvarea în meciuri_azi.csv: {e}")

cached_matches = []
last_fetch_time = None

# ==============================================================================
# RUTE FIȘIERE STATICE
# ==============================================================================
@app.get("/")
def read_index():
    return FileResponse("index.html")

@app.get("/style.css")
def read_css():
    return FileResponse("style.css")

@app.get("/app.js")
def read_js():
    return FileResponse("app.js")

@app.get("/manifest.json")
def read_manifest():
    return FileResponse("manifest.json")

# ==============================================================================
# ENDPOINT: LISTA MECIURI (FLASHSCORE / LIVESCORE HYBRID PARSER)
# ==============================================================================
@app.get("/api/matches") 
def get_rapidapi_matches():
    global cached_matches, last_fetch_time

    league_accuracy = load_league_confidence_thresholds()

    romania_tz = timezone(timedelta(hours=3))
    now = datetime.now(romania_tz)
    today_api_str = now.strftime("%Y-%m-%d")

    url = "https://flashscore4.p.rapidapi.com/api/flashscore/v2/matches/list-by-date"

    querystring = {
        "sport_id": "1",
        "date": today_api_str,
        "timezone": "Europe/Bucharest"
    }

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "flashscore4.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    print(f"--> Apelăm API pentru data: {today_api_str}...")
    parsed_matches = []

    try:
        response = requests.get(url, headers=headers, params=querystring)
        print(f"--> Status Code API: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            raw_matches_count = 0

            # data este o listă de turnee
            tournaments = data if isinstance(data, list) else data.get("DATA", data.get("Stages", []))

            for stage in tournaments:
                if not isinstance(stage, dict):
                    continue

                league_name = stage.get("name") or stage.get("NAME") or stage.get("Cnm") or "Fotbal Generat"
                
                # Meciurile sunt în lista 'matches'
                matches_list = stage.get("matches", [])

                for item in matches_list:
                    if not isinstance(item, dict):
                        continue

                    raw_matches_count += 1

                    # Extragere nume echipe din dicționarele 'home_team' și 'away_team'
                    home_obj = item.get("home_team", {})
                    away_obj = item.get("away_team", {})

                    home_str = home_obj.get("name") if isinstance(home_obj, dict) else str(home_obj)
                    away_str = away_obj.get("name") if isinstance(away_obj, dict) else str(away_obj)

                    if not home_str or not away_str:
                        home_str = "Gazde"
                        away_str = "Oaspeți"

                    # Filtru tineret / rezerve
                    if any(p in home_str.lower() or p in away_str.lower() for p in [" ii", " 2", " b ", " u21", " u19"]):
                        continue

                    # Extragere Oră din timestamp
                    timestamp = item.get("timestamp")
                    if timestamp:
                        match_dt = datetime.fromtimestamp(timestamp, tz=romania_tz)
                        match_time = match_dt.strftime("%H:%M")
                    else:
                        match_time = "19:00"

                     # Indici Statistici Deterministici (simulați pe baza numelor echipelor) 
                    seed_val = sum(ord(c) for c in (home_str + away_str))
                    rng = random.Random(seed_val)
                    
                    p_15 = round(rng.uniform(62.0, 91.0), 2)
                    p_25 = round(rng.uniform(42.0, 78.0), 2)
                    p_ht = round(rng.uniform(55.0, 88.0), 2) # Forma / Dominanță Pauză
                    p_st = round(rng.uniform(48.0, 82.0), 2) # Forma / Dominanță Repriza 2
                    p_gg = round(rng.uniform(38.0, 72.0), 2)

                    # Calcul Pronostic FĂRĂ COTE
                    pred = calculate_ai_prediction(p_15, p_25, p_gg, p_ht, p_st)

                    acc = league_accuracy.get(str(league_name), 50.0)
                    conf = "Ridicată" if (acc >= 65.0 or p_15 >= 80.0 or p_25 >= 72.0) else "Medie"

                    parsed_matches.append({
                        "datetime": f"Azi, {match_time}",
                        "league": str(league_name),
                        "homeTeam": home_str,
                        "awayTeam": away_str,
                        "prediction": pred,
                        "confidence": conf,
                        "stats": {
                            "p_15": p_15,
                            "p_25": p_25,
                            "p_gg": p_gg
                        }
                    })


            print(f"--> S-au identificat {raw_matches_count} meciuri brute în JSON-ul API-ului.")
            cached_matches = parsed_matches
            last_fetch_time = now
            print(f"--> Total meciuri relevante procesate și afișate: {len(parsed_matches)}")

            save_matches_to_csv(parsed_matches)
        else:
            print(f"--> Eroare API {response.status_code}: {response.text}")

    except Exception as e:
        print(f"--> Excepție întâmpinată: {e}")

    return parsed_matches

# ==============================================================================
# ENDPOINT: STATISTICI & ANALYTICS AI (MODAL)
# ==============================================================================
@app.get("/api/match-analytics")
def get_match_analytics(home: str, away: str):
    seed_val = sum(ord(c) for c in (home + away))
    rng = random.Random(seed_val)

    p_15 = round(rng.uniform(62.0, 91.0), 2)
    p_25 = round(rng.uniform(42.0, 78.0), 2)
    p_ht = round(rng.uniform(55.0, 88.0), 2)
    p_st = round(rng.uniform(48.0, 82.0), 2)
    p_gg = round(rng.uniform(38.0, 72.0), 2)
    p_cards = round(rng.uniform(18.0, 58.0), 2)
    p_corners = round(rng.uniform(22.0, 65.0), 2)

    def get_color(val):
        if val >= 65.0:
            return "green"
        elif val >= 45.0:
            return "orange"
        return "red"

    return {
        "teams": {"home": home, "away": away},
        "overall_probabilities": [
            {"label": "Peste 1.5 Goluri", "val": p_15, "color": get_color(p_15)},
            {"label": "Peste 2.5 Goluri", "val": p_25, "color": get_color(p_25)},
            {"label": "Peste 0.5 Repriza 1", "val": p_ht, "color": get_color(p_ht)},
            {"label": "Peste 0.5 Repriza 2", "val": p_st, "color": get_color(p_st)},
            {"label": "Ambele Marchează (GG)", "val": p_gg, "color": get_color(p_gg)},
            {"label": "Peste 3.5 Cartonașe", "val": p_cards, "color": get_color(p_cards)},
            {"label": "Peste 9.5 Cornere", "val": p_corners, "color": get_color(p_corners)}
        ]
    }

# ==============================================================================
# PORNIRE SERVER
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
