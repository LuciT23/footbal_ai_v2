from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
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

# PUNE CHEIA TA API AICI ÎNTRE GHILIMELE:
API_KEY = "PUNE_AICI_API_KEY_UL_TAU"

@app.get("/api/matches")
def get_football_data_matches():
    # Preluăm meciurile viitoare din Premier League (PL)
    # Alte coduri de ligi: 'PD' (La Liga), 'SA' (Serie A), 'BL1' (Bundesliga), 'CL' (Champions League)
    url = "https://api.football-data.org/v4/competitions/PL/matches?status=SCHEDULED"
    
    headers = {
        "X-Auth-Token": 59b1d7e200f549c9a4bd4fe4d243c565
    }
    
    parsed_matches = []
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code Football-Data: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get("matches", [])
            
            # Preluăm primele 10 meciuri programate
            for match in matches[:10]:
                home_team = match.get("homeTeam", {}).get("name", "Gazde")
                away_team = match.get("awayTeam", {}).get("name", "Oaspeți")
                
                # Formatare dată și oră
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
                    "odds1": "1.85", # Punct de extindere pentru cote
                    "oddsX": "3.50",
                    "odds2": "4.10",
                    "prediction": "1 (Vic. Gazde)",
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
