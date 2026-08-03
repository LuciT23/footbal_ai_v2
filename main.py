import random
import requests
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import requests
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAPIDAPI_KEY = "2ac6bb003amshea4487405e15e1fp18b95ejsn700b80898b4a"

cached_matches = []
last_fetch_time = None

@app.get("/")
def read_index():
    return FileResponse("index.html")

@app.get("/style.css")
def read_css():
    return FileResponse("style.css")

@app.get("/app.js")
def read_js():
    return FileResponse("app.js")

@app.get("/api/matches") 
def get_rapidapi_matches():
    global cached_matches, last_fetch_time
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
            
            # Căutăm recursiv orice obiect din JSON care are un meci/echipe
            def extract_matches(obj):
                if isinstance(obj, list):
                    for item in obj:
                        extract_matches(item)
                elif isinstance(obj, dict):
                    # Verificăm diverse structuri posibile din API-uri
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

                # 2. Extragere Ligă
                league_name = (
                    item.get("cname") or 
                    item.get("competition_name") or 
                    (item.get("competition", {}).get("name") if isinstance(item.get("competition"), dict) else "Fotbal Generat")
                )

                # Afișăm în terminal ce meci și ce ligă am găsit pentru inspecție
                print(f"[GASIT] Liga: '{league_name}' | Meci: {home_team} vs {away_team}")

                date_start = item.get("datestart", "")
                match_time = date_start.split(" ")[1][:5] if " " in date_start else "19:00"
                
                match_data = {
                    "datetime": f"Azi, {match_time}",
                    "league": str(league_name),
                    "homeTeam": str(home_team),
                    "awayTeam": str(away_team),
                    "odds1": "2.10",
                    "oddsX": "3.25",
                    "odds2": "3.50",
                    "prediction": "1X",
                    "confidence": "Mare"
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

@app.get("/api/match-analytics") 
def get_match_analytics(home: str, away: str):
    """
    Generăm procentaje unice și dinamice pentru fiecare meci în parte, 
    folosind numele echipelor ca 'seed'.
    """
    # Cream un număr unic derivat din numele celor două echipe
    seed_val = sum(ord(c) for c in (home + away))
    rng = random.Random(seed_val)
    
    # Generăm procentaje realiste, unice per meci
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
import random 

