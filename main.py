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
    
    if last_fetch_time and (now - last_fetch_time).total_seconds() < 1800 and cached_matches:
        print("--> Returnăm datele salvate din cache.")
        return cached_matches

    today_str = now.strftime("%Y-%m-%d")
    
    url = "https://api-football186.p.rapidapi.com/competition_matches_list"
    
    headers = {
        "x-rapidapi-key": "2ac6bb003amshea4487405e15e1fp18b95ejsn700b80898b4a",
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
            
            # Printăm în consolă structura exactă primită pentru verificare
            print("--> Structură răspuns primita:", type(data))
            
            # Identificare automată listă meciuri
            raw_list = []
            if isinstance(data, list):
                raw_list = data
            elif isinstance(data, dict):
                # Căutăm lista în cheile comune
                for key in ["data", "result", "response", "matches", "events"]:
                    if key in data and isinstance(data[key], list):
                        raw_list = data[key]
                        break
                # Dacă nu găsim o cheie cunoscută, luăm prima listă găsită în dicționar
                if not raw_list:
                    for val in data.values():
                        if isinstance(val, list):
                            raw_list = val
                            break

            print(f"--> Meciuri extrase din JSON: {len(raw_list)}")
            
            for item in raw_list[:25]:
                if not isinstance(item, dict):
                    continue
                    
                home_team = item.get("home_team_name", item.get("home_name", item.get("home", "Gazde")))
                away_team = item.get("away_team_name", item.get("away_name", item.get("away", "Oaspeți")))
                league_name = item.get("league_name", item.get("competition_name", item.get("competition", "Fotbal")))
                match_time = item.get("time", item.get("match_time", item.get("status", "Azi")))
                
                parsed_matches.append({
                    "datetime": f"Azi, {match_time}",
                    "league": league_name,
                    "homeTeam": home_team,
                    "awayTeam": away_team,
                    "odds1": "2.10",
                    "oddsX": "3.25",
                    "odds2": "3.50",
                    "prediction": "1X",
                    "confidence": "Mare"
                })
                
            cached_matches = parsed_matches
            last_fetch_time = now
        else:
            print(f"--> Eroare API {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"--> Excepție întâmpinată: {e}")
        
    return parsed_matches

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
