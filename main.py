from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import requests
from datetime import datetime
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectăm folderele css și js pentru a putea fi citite de browser
if os.path.exists("css"):
    app.mount("/css", StaticFiles(directory="css"), name="css")
if os.path.exists("js"):
    app.mount("/js", StaticFiles(directory="js"), name="js")

# PUNE CHEIA TA API AICI:
API_KEY = "PUNE_AICI_CHEIA_TA_FOOTBALL_DATA"

# Când deschizi adresa principală (/), trimitem fișierul index.html
@app.get("/")
def read_index():
    return FileResponse("index.html")

@app.get("/api/matches")
def get_football_data_matches():
    url = "https://api.football-data.org/v4/competitions/PL/matches?status=SCHEDULED"
    headers = {"X-Auth-Token": API_KEY}
    parsed_matches = []
    
    try:
        response = requests.get(url, headers=headers)
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
                    "prediction": "1 (Vic. Gazde)",
                    "confidence": "Mare"
                })
        else:
            print(f"Eroare API: {response.status_code}")
    except Exception as e:
        print(f"Excepție: {e}")
        
    return parsed_matches

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
