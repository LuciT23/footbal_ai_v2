from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
import requests
from datetime import datetime

app = FastAPI()

# Permitem accesul din interfața Web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_sofascore_matches():
    # Endpoint-ul SofaScore pe care l-ai găsit
    url = "https://www.sofascore.com/api/v1/unique-tournament/13470/scheduled-events/2026-07-29"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }
    
    parsed_matches = []
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            events = data.get("events", [])
            
            for event in events:
                home_team = event.get("homeTeam", {}).get("name", "Gazde")
                away_team = event.get("awayTeam", {}).get("name", "Oaspeți")
                
                # Formatare oră meci
                timestamp = event.get("startTimestamp")
                match_time = datetime.fromtimestamp(timestamp).strftime("%H:%M") if timestamp else "Azi"
                
                parsed_matches.append({
                    "datetime": f"Azi, {match_time}",
                    "league": "premier-league",
                    "homeTeam": home_team,
                    "awayTeam": away_team,
                    "odds1": "1.95", # Cotele pot fi extrase separat per meci
                    "oddsX": "3.40",
                    "odds2": "3.80",
                    "prediction": "Vic. Gazde",
                    "confidence": "Mare"
                })
        else:
            print(f"Eroare API SofaScore: {response.status_code}")
    except Exception as e:
        print(f"Excepție întâmpinată: {e}")
        
    return parsed_matches

@app.get("/api/matches")
def get_matches():
    # Trimite meciurile din API-ul SofaScore către Frontend
    return get_sofascore_matches()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
