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

# Lipeste AICI cheia ta de la RapidAPI (X-RapidAPI-Key):
RAPIDAPI_KEY = "2ac6bb003amshea4487405e15e1fp18b95ejsn700b80898b4a"

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
def get_sofascore_rapidapi_matches():
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Endpoint de la Sofascore ApiDojo pe RapidAPI pentru meciurile de azi
    url = "https://sofascore3.p.rapidapi.com/matches/list-by-date"
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "sofascore3.p.rapidapi.com"
    }
    
    params = {"date": today}
    parsed_matches = []
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"Status Code RapidAPI Sofascore: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            events = data.get("events", [])
            
            # Luăm primele 15 meciuri de azi
            for event in events[:15]:
                home_team = event.get("homeTeam", {}).get("name", "Gazde")
                away_team = event.get("awayTeam", {}).get("name", "Oaspeți")
                tournament = event.get("tournament", {}).get("name", "Fotbal")
                
                timestamp = event.get("startTimestamp")
                if timestamp:
                    match_time = datetime.fromtimestamp(timestamp).strftime("%H:%M")
                else:
                    match_time = "Azi"
                
                parsed_matches.append({
                    "datetime": f"Azi, {match_time}",
                    "league": tournament,
                    "homeTeam": home_team,
                    "awayTeam": away_team,
                    "odds1": "2.05",
                    "oddsX": "3.25",
                    "odds2": "3.60",
                    "prediction": "1X",
                    "confidence": "Mare"
                })
        else:
            print(f"Eroare API: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Excepție: {e}")
        
    return parsed_matches

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
