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
    
    # Cuvinte cheie pentru prioritizare în topul tabelului
    TOP_KEYWORDS = [
        "romania", "ro", "superliga", "liga 1", "cupa",
        "uefa", "champions", "europa", "conference", 
        "england", "spain", "italy", "germany", "france",
        "premier", "la liga", "serie a", "bundesliga", "ligue"
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
            
            top_matches = []
            other_matches = []
            
            for item in matches_found:
                teams = item.get("teams", {})
                home_team = teams.get("home", {}).get("tname", "Gazde")
                away_team = teams.get("away", {}).get("tname", "Oaspeți")
                
                league_name = (
                    item.get("cname") or 
                    (item.get("competition", {}).get("name") if isinstance(item.get("competition"), dict) else "Fotbal")
                )
                
                league_lower = str(league_name).lower()
                
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
                
                # Verificăm dacă liga este una importantă
                is_priority = any(kw in league_lower for kw in TOP_KEYWORDS)
                
                if is_priority:
                    top_matches.append(match_data)
                else:
                    other_matches.append(match_data)
            
            # Punem meciurile importante primele, urmate de restul
            parsed_matches = top_matches + other_matches
                
            cached_matches = parsed_matches
            last_fetch_time = now
            print(f"--> Am încărcat {len(parsed_matches)} meciuri ({len(top_matches)} din ligi principale)!")
        else:
            print(f"--> Eroare API {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"--> Excepție întâmpinată: {e}")
        
    return parsed_matches

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
