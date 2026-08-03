import os 
import csv
import random
import requests
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(title="Football AI Prediction API")

# Permitem cereri CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAPIDAPI_KEY = "2ac6bb003amshea4487405e15e1fp18b95ejsn700b80898b4a"

# ==============================================================================
# FUNCTIA DE MEMORIE & ÎNVĂȚARE (CITIRE DIN ISTORIC_INVATARE.CSV)
# ==============================================================================
def load_league_confidence_thresholds():
    """
    Citește istoric_invatare.csv și calculează procentul de câștig per ligă.
    Dacă o ligă are rată de succes > 70%, ajustăm pragul pentru 'Confidence Mare'.
    """
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


cached_matches = []
last_fetch_time = None

# ==============================================================================
# FIȘIERE STATICE / RUTE INDEX
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


# ==============================================================================
# ENDPOINT: LISTA MECIURI
# ==============================================================================
@app.get("/api/matches")
def get_rapidapi_matches():
    global cached_matches, last_fetch_time
    
    # 1. Citim istoricul de invatare din CSV per liga
    league_accuracy = load_league_confidence_thresholds()
    
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    url = "https://api-football186.p.rapidapi.com/competition_matches_list"
   
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "api-football186.p.rapidapi.com"
    }
   
    querystring = {
        "date": today_str,
        "timezone": "+03:00"
    }
   
    print(f"--> Apelăm API pentru data: {today_str}...")
    parsed_matches = []
   
    try:
        response = requests.get(url, headers=headers, params=querystring)
        print(f"--> Status Code API: {response.status_code}")
       
        if response.status_code == 200:
            data = response.json()
            matches_found = []
           
            def extract_matches(obj):
                if isinstance(obj, list):
                    for item in obj:
                        extract_matches(item)
                elif isinstance(obj, dict):
                    if "teams" in obj or "home" in obj or "homeTeam" in obj:
                        matches_found.append(obj)
                    else:
                        for val in obj.values():
                            extract_matches(val)

            extract_matches(data)
            print(f"--> S-au identificat {len(matches_found)} meciuri brute în JSON-ul API-ului.")
           
            for item in matches_found:
                # 1. Extragere Echipe
                teams = item.get("teams", {})
                if isinstance(teams, dict):
                    home_team = teams.get("home", {}).get("tname") or teams.get("home", {}).get("name") or item.get("homeTeam", "Gazde")
                    away_team = teams.get("away", {}).get("tname") or teams.get("away", {}).get("name") or item.get("awayTeam", "Oaspeți")
                else:
                    home_team = item.get("homeTeam", "Gazde")
                    away_team = item.get("awayTeam", "Oaspeți")

                home_str = str(home_team)
                away_str = str(away_team)

                # Excludem echipele secundare (ex: Earthquakes II)
                if any(p in home_str.lower() or p in away_str.lower() for p in [" ii", " 2", " b ", " u21", " u19"]):
                    continue

                # 2. Extragere Ligă
                league_name = (
                    item.get("cname") or
                    item.get("competition_name") or
                    (item.get("competition", {}).get("name") if isinstance(item.get("competition"), dict) else "Fotbal Generat")
                )

                date_start = item.get("datestart", "")
                match_time = date_start.split(" ")[1][:5] if " " in date_start and len(date_start.split(" ")) > 1 else "19:00"
               
                # 3. Extragere/Generare Cote Dinamice
                odds_data = item.get("odds", {})
                o1 = odds_data.get("1") or f"{round(random.uniform(1.40, 3.20), 2):.2f}"
                ox = odds_data.get("X") or f"{round(random.uniform(3.10, 4.10), 2):.2f}"
                o2 = odds_data.get("2") or f"{round(random.uniform(1.80, 4.80), 2):.2f}"
                
                # 4. Calculare Pronostic
                float_o1 = float(o1)
                float_o2 = float(o2)
                if float_o1 < 1.80:
                    pred = "1"
                elif float_o2 < 1.80:
                    pred = "2"
                else:
                    pred = "1X" if float_o1 <= float_o2 else "X2"

                # 5. Calculare Încredere bazată pe Istoricul Ligii din CSV
                acc = league_accuracy.get(str(league_name), 50.0)
                if acc >= 70.0 or float_o1 <= 1.70:
                    conf = "Mare"
                else:
                    conf = "Mediu"

                match_data = {
                    "datetime": f"Azi, {match_time}",
                    "league": str(league_name),
                    "homeTeam": home_str,
                    "awayTeam": away_str,
                    "odds1": str(o1),
                    "oddsX": str(ox),
                    "odds2": str(o2),
                    "prediction": pred,
                    "confidence": conf
                }
               
                parsed_matches.append(match_data)
               
            cached_matches = parsed_matches
            last_fetch_time = now
            print(f"--> Total meciuri procesate și afișate: {len(parsed_matches)}")
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
    """
    Generăm procentaje unice și dinamice pentru fiecare meci în parte,
    folosind numele echipelor ca 'seed'.
    """
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

    analytics = {
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
   
    return analytics


# ==============================================================================
# PORNIRE SERVER
# ==============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
