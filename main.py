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
# Filtru pentru eliminarea ligilor inferioare / neimportante
# ==============================================================================
ALLOWED_LEAGUES = [
    # Top Campionate & Ligi Europene
    "premier league", "la liga", "serie a", "bundesliga", "ligue 1",
    "championship", "2. bundesliga", "serie b", "segunda division",
    "eredivisie", "liga portugal", "pro league", "super lig", "premiership",
    "Superliga",
   
    # România
    "liga 1", "superliga", "liga i",
   
    # Cupe Europene & Internaționale
    "champions league", "europa league", "conference league", "nations league",
   
    # America de Sud & Altele populare
    "brasileiro", "serie a brazil", "copa libertadores", "copa sudamericana", "mls"
]

# ==============================================================================
# 1. FUNCTIA DE MEMORIE & ÎNVĂȚARE (CITIRE DIN ISTORIC_INVATARE.CSV)
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

# ==============================================================================
# 2. MOTORUL DE DECIZIE AI (CALCUL PRONOSTIC BAZAT PE STATISTICI)
# ==============================================================================
def calculate_ai_prediction(p_15, p_25, p_gg, p_ht, o1, o2):
    """
    Stabilește cel mai bun pronostic analizând probabilitățile statistice,
    nu doar cotele 1X2.
    """
    float_o1 = float(o1)
    float_o2 = float(o2)

    # 1. Meci clar de goluri multe
    if p_25 >= 72.0 and p_gg >= 60.0:
        return "Peste 2.5"
   
    # 2. Ambele echipe marchează
    if p_gg >= 68.0:
        return "GG"

    # 3. Favorită clară acasă
    if float_o1 <= 1.65 or (p_ht >= 80.0 and float_o1 < 2.10):
        return "1"

    # 4. Favorită clară în deplasare
    if float_o2 <= 1.65:
        return "2"

    # 5. Meci moderat de goluri (Cel mai sigur din punct de vedere statistic)
    if p_15 >= 75.0:
        return "Peste 1.5"

    # 6. Default: Șansă dublă acoperită
    return "1X" if float_o1 <= float_o2 else "X2"

# ==============================================================================
# 3. SALVARE AUTOMATĂ MECIURI ÎN MECIURI_AZI.CSV
# ==============================================================================
def save_matches_to_csv(matches):
    """
    Salvează meciurile filtrate de azi în meciuri_azi.csv pentru verificarea ulterioară.
    """
    file_path = "meciuri_azi.csv"
    file_exists = os.path.exists(file_path)

    existing_keys = set()
    if file_exists:
        try:
            with open(file_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = f"{row.get('data')}_{row.get('liga')}_{row.get('echipa_gazda')}_{row.get('echipa_oaspete')}"
                    existing_keys.add(key)
        except Exception as e:
            print(f"--> Eroare la citirea meciuri_azi.csv: {e}")

    today_str = datetime.now().strftime("%Y-%m-%d")

    try:
        with open(file_path, mode="a", newline="", encoding="utf-8") as f:
            fieldnames = ["data", "liga", "echipa_gazda", "echipa_oaspete", "pronostic", "cota", "status"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            added_count = 0
            for m in matches:
                key = f"{today_str}_{m['league']}_{m['homeTeam']}_{m['awayTeam']}"
                if key not in existing_keys:
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
                    existing_keys.add(key)
                    added_count += 1

            if added_count > 0:
                print(f"--> [AUTO-SAVE] S-au salvat {added_count} meciuri noi în 'meciuri_azi.csv'.")
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
    
@app.get("manifest.json")
def read_manifest():
    return FileResponse("manifest.json")
    
# ==============================================================================
# ENDPOINT: LISTA MECIURI (ADAPTAT PENTRU LIVESCORE API)
# ==============================================================================
@app.get("/api/matches")
def get_rapidapi_matches():
    global cached_matches, last_fetch_time
   
    league_accuracy = load_league_confidence_thresholds()

    romania_tz = timezone(timedelta(hours=3))
    now = datetime.now(romania_tz)
    today_str = now.strftime("%Y-%m-%d")

    print(f"-->[Verificare] Se solicita meciurile pentru data de AZI: {today_api_str}")
    
    url = "https://livescore6.p.rapidapi.com/matches/v2/list-by-date"  

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "livescore6.p.rapidapi.com"
    }

    querystring = {
        "date": today_str,
        "timezone": "+03:00"
    }

    response = requests.get(url, headers=headers, params=quertstring)

    print(f"--> Apelăm API pentru data: {today_str}...")
    parsed_matches = []

    try:
        response = requests.get(url, headers=headers, params=querystring)
        print(f"--> Status Code API: {response.status_code}")
     
        if response.status_code == 200:
            data = response.json()
            stages = data.get("Stages", [])
            
            raw_matches_count = 0

            # 1. Trecem prin fiecare Ligă/Competiție (Stage)
            for stage in stages:
                league_name = stage.get("Cnm") or stage.get("Snm") or "Fotbal Generat"
                events = stage.get("Events", [])

                # 2. Trecem prin fiecare Meci (Event) din ligă
                for item in events:
                    raw_matches_count += 1
                    
                    # FILTRARE WHITELIST (LIGI PERMISE) - opțional
                    # league_lower = str(league_name).lower()
                    # if not any(allowed in league_lower for allowed in ALLOWED_LEAGUES):
                    # continue

                    # Extragere Echipe din T1 (Gazde) și T2 (Oaspeți)
                    t1_list = item.get("T1", [])
                    t2_list = item.get("T2", [])

                    home_team = t1_list[0].get("Nm", "Gazde") if isinstance(t1_list, list) and len(t1_list) > 0 else "Gazde"
                    away_team = t2_list[0].get("Nm", "Oaspeți") if isinstance(t2_list, list) and len(t2_list) > 0 else "Oaspeți"

                    home_str = str(home_team)
                    away_str = str(away_team)

                    # Excludem meciurile de tineret sau rezervă
                    if any(p in home_str.lower() or p in away_str.lower() for p in [" ii", " 2", " b ", " u21", " u19"]):
                        continue

                    # Extragere oră meci (Esd contine timestamp de tip 20260804190000)
                    esd = str(item.get("Esd", ""))
                    if len(esd) >= 12:
                        match_time = f"{esd[8:10]}:{esd[10:12]}"
                    else:
                        match_time = "19:00"

                    # Extragere / Generare Cote
                    o1 = f"{round(random.uniform(1.40, 3.20), 2):.2f}"
                    ox = f"{round(random.uniform(3.10, 4.10), 2):.2f}"
                    o2 = f"{round(random.uniform(1.80, 4.80), 2):.2f}"

                    # Generare Statistici Deterministice (Seed per meci)
                    seed_val = sum(ord(c) for c in (home_str + away_str))
                    rng = random.Random(seed_val)
                    p_15 = round(rng.uniform(62.0, 91.0), 2)
                    p_25 = round(rng.uniform(42.0, 78.0), 2)
                    p_ht = round(rng.uniform(55.0, 88.0), 2)
                    p_gg = round(rng.uniform(38.0, 72.0), 2)

                    # Calcul Pronostic Inteligent
                    pred = calculate_ai_prediction(p_15, p_25, p_gg, p_ht, o1, o2)

                    # Calcul Încredere
                    acc = league_accuracy.get(str(league_name), 50.0)
                    if acc >= 70.0 or p_15 >= 80.0 or float(o1) <= 1.65:
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

            print(f"--> S-au identificat {raw_matches_count} meciuri brute în JSON-ul API-ului.")
            cached_matches = parsed_matches
            last_fetch_time = now
            print(f"--> Total meciuri relevante procesate și afișate: {len(parsed_matches)}")

            # SALVARE AUTOMATĂ
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
