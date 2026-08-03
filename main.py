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
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "api-football186.p.rapidapi.com"
    }
    
    querystring = {
        "date": today_str,
        "timezone": "+03:00"
    }
    
    print(f"--> Apelăm API pentru data: {today_str}...")
    parsed_matches = []
    
    # Lista de cuvinte cheie pentru ligile de top pe care le vrem în aplicație
    TOP_LEAGUES_KEYWORDS = [
        "romania", "superliga", "liga i", "cupa romaniei",
        "champions league", "europa league", "conference league", "uefa",
        "premier league", "la liga", "serie a", "bundesliga", "ligue 1",
        "eredivisie", "primeira liga", "pro league", "super lig"
    ]
    
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
                    if "teams" in obj and isinstance(obj["teams"], dict):
                        matches_found.append(obj)
                    else:
                        for val in obj.values():
                            extract_matches(val)

            extract_matches(data)
            
            for item in matches_found:
                teams = item.get("teams", {})
                home_team = teams.get("home", {}).get("tname", "Gazde")
                away_team = teams.get("away", {}).get("tname", "Oaspeți")
                
                league_name = (
                    item.get("cname") or 
                    (item.get("competition", {}).get("name") if isinstance(item.get("competition"), dict) else "Fotbal")
                )
                
                league_lower = str(league_name).lower()
                
                # Excludem explicit ligile secundare/secundare din Brazilia/alte țări dacă conțin "serie b", "2", "division 2"
                if "serie b" in league_lower or "liga 2" in league_lower or "2. bundesliga" in league_lower:
                    continue
                
                # Verificăm dacă liga face parte din cele de top doriți
                is_top_league = any(kw in league_lower for kw in TOP_LEAGUES_KEYWORDS)
                
                # Dacă nu e în lista de top, o ignorăm pentru a păstra lista curată
                if not is_top_league:
                    continue

                date_start = item.get("datestart", "")
                match_time = date_start.split(" ")[1][:5] if " " in date_start else "Azi"
                
                match_data = {
                    "datetime": f"Azi, {match_time}",
                    "league": str(league_name),
                    "homeTeam": home_team,
                    "awayTeam": away_team,
                    "odds1": "2.10",
                    "oddsX": "3.25",
                    "odds2": "3.50",
                    "prediction": "1X",
                    "confidence": "Mare"
                }
                
                # Prioritizare: România & UEFA la începutul listei
                if any(k in league_lower for k in ["romania", "superliga", "liga i", "uefa", "champions", "europa"]):
                    parsed_matches.insert(0, match_data)
                else:
                    parsed_matches.append(match_data)
                
            cached_matches = parsed_matches
            last_fetch_time = now
            print(f"--> Am filtrat și încărcat {len(parsed_matches)} meciuri importante!")
        else:
            print(f"--> Eroare API {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"--> Excepție întâmpinată: {e}")
        
    return parsed_matches


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
