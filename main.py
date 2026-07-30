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

# Pune AICI cheia ta unică de pe RapidAPI:
RAPIDAPI_KEY = "PUNE_AICI_CHEIA_TA_RAPIDAPI"

# Memorie Cache pentru a economisi din limita de cereri
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
def get_api_football_matches():
    global cached_matches, last_fetch_time
    
    now = datetime.now()
    
    # Dacă avem meciuri salvate mai noi de 30 de minute (1800 secunde), le returnăm pe cele din memorie
    if last_fetch_time and (now - last_fetch_time).total_seconds() < 1800 and cached_matches:
        print("--> Returnăm datele salvate din cache (fără request la API).")
        return cached_matches

    # Altfe, facem o cerere nouă către API-FOOTBALL
    today_str = now.strftime("%Y-%m-%d")
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    
    params = {"date": today_str}
    
    print(f"--> Facem un request nou către API-FOOTBALL pentru data: {today_str}...")
    
    parsed_matches = []
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"--> Status Code API-Football: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            fixtures = data.get("response", [])
            print(f"--> Am găsit {len(fixtures)} meciuri pentru azi!")
            
            # Luăm primele 25 de meciuri de azi
            for item in fixtures[:25]:
                fixture = item.get("fixture", {})
                teams = item.get("teams", {})
                league = item.get("league", {})
                
                home_team = teams.get("home", {}).get("name", "Gazde")
                away_team = teams.get("away", {}).get("name", "Oaspeți")
                league_name = league.get("name", "Fotbal")
                
                date_str = fixture.get("date")
                if date_str:
                    # Formatare oră meci (ex: 19:45)
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    match_time = dt.strftime("%H:%M")
                else:
                    match_time = "Azi"
                
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
                
            # Salvăm datele în cache
            cached_matches = parsed_matches
            last_fetch_time = now
            
        else:
            print(f"--> Eroare API: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"--> Excepție întâmpinată: {e}")
        
    return parsed_matches

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
