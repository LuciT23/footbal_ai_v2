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

# PUNE CHEIA TA API AICI:
API_KEY = "PUNE_AICI_CHEIA_TA_FOOTBALL_DATA"

# Rute pentru fișierele din rădăcină
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
def get_football_data_matches():
    url = "https://api.football-data.org/v4/competitions/PL/matches?status=SCHEDULED"
    headers = {"X-Auth-Token": API_KEY}
    parsed_matches = []
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code Football-Data: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get("matches", [])
            
            for match in matches[:10]:
                home_team = match.get("homeTeam", {}).get("name", "Gazde")
                away_team = match.get("awayTeam", {}).get("name", "Oaspeți")
                
                utc_date = match.get("utcDate")
                if utc_date:
                    dt = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ")
                    match_time = dt.strftime("%d %b, %H:%M")
                else:
                    match_time = "Curând"
                
                parsed_matches.append({
                    "datetime": match_time,
                    "league": "premier-league",
                    "homeTeam": home_team,
                    "awayTeam": away_team,
                    "odds1": "1.85",
                    "oddsX": "3.50",
                    "odds2": "4.10",
                    "prediction": "Vic. Gazde",
                    "confidence": "Mare"
                })
        else:
            print(f"Eroare API: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Excepție întâmpinată: {e}")
        
    return parsed_matches

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
