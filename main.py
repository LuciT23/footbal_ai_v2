from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# Permite interfeței tale HTML (care rulează pe alt port/local) să acceseze API-ul
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def scrape_live_odds():
    """
    Exemplu de funcție de scraping. 
    Aici înlocuiești URL-ul și selectorii cu site-ul dorit.
    """
    # Exemplu simulat de extragere de date
    # În producție folosești requests.get(URL) + BeautifulSoup(response.text, 'html.parser')
    
    matches = [
        {
            "datetime": "Azi, 21:00",
            "league": "premier-league",
            "homeTeam": "Arsenal",
            "awayTeam": "Liverpool",
            "odds1": "2.10",
            "oddsX": "3.30",
            "odds2": "3.20",
            "prediction": "Peste 2.5 goluri",
            "confidence": "Mare"
        },
        {
            "datetime": "Azi, 22:00",
            "league": "la-liga",
            "homeTeam": "Real Madrid",
            "awayTeam": "Barcelona",
            "odds1": "1.95",
            "oddsX": "3.60",
            "odds2": "3.70",
            "prediction": "Ambele Marchează",
            "confidence": "Mare"
        }
    ]
    return matches

@app.get("/api/matches")
def get_matches():
    # Când frontend-ul cere datele, rulați scraperul și returnăm datele
    live_data = scrape_live_odds()
    return live_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

