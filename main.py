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
            matches_found = []
            
            def extract_matches(obj):
                if isinstance(obj, list):
                    for item in obj:
                        extract_matches(item)
                elif isinstance(obj, dict):
                    # Identificăm dacă obiectul reprezintă un meci
                    if any(k in obj for k in ["teama", "team_a", "home_team", "home", "homeTeam", "teams"]):
                        matches_found.append(obj)
                    else:
                        for val in obj.values():
                            extract_matches(val)

            extract_matches(data)
            print(f"--> Meciuri identificate: {len(matches_found)}")
            
            for item in matches_found:
                # Extragere nume echipa gazdă
                home = (
                    item.get("teama", {}).get("name") if isinstance(item.get("teama"), dict) else
                    item.get("home_team", {}).get("name") if isinstance(item.get("home_team"), dict) else
                    item.get("teama") or item.get("home_team_name") or item.get("home_name") or item.get("home") or item.get("team_a")
                )
                
                # Extragere nume echipa oaspete
                away = (
                    item.get("teamb", {}).get("name") if isinstance(item.get("teamb"), dict) else
                    item.get("away_team", {}).get("name") if isinstance(item.get("away_team"), dict) else
                    item.get("teamb") or item.get("away_team_name") or item.get("away_name") or item.get("away") or item.get("team_b")
                )
                
                # Extragere ligă
                league = (
                    item.get("competition", {}).get("name") if isinstance(item.get("competition"), dict) else
                    item.get("cname") or item.get("league_name") or item.get("competition_name") or item.get("competition") or "Fotbal"
                )
                
                # Ora meciului
                match_time = item.get("time") or item.get("status_str") or item.get("status") or "Azi"
                
                # Fallback în caz că numele sunt numere sau lipsesc
                home_str = str(home) if home and not str(home).isdigit() else "Gazde"
                away_str = str(away) if away and not str(away).isdigit() else "Oaspeți"
                league_str = str(league) if league else "Fotbal"
                
                # Dacă am găsit cel puțin un nume valid de echipă, adăugăm meciul
                if home_str != "Gazde" or away_str != "Oaspeți":
                    parsed_matches.append({
                        "datetime": f"Azi, {match_time}",
                        "league": league_str,
                        "homeTeam": home_str,
                        "awayTeam": away_str,
                        "odds1": "2.10",
                        "oddsX": "3.25",
                        "odds2": "3.50",
                        "prediction": "1X",
                        "confidence": "Mare"
                    })
                
            cached_matches = parsed_matches
            last_fetch_time = now
            print(f"--> Am procesat cu succes {len(parsed_matches)} meciuri cu nume reale!")
        else:
            print(f"--> Eroare API {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"--> Excepție întâmpinată: {e}")
        
    return parsed_matches


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
