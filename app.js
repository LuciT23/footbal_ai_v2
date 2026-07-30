// Elemente din DOM 
const tableBody = document.getElementById("matches-table-body");
const leagueSelect = document.getElementById("league-select");
const currentLeagueText = document.getElementById("current-league");

// Variabilă globală pentru a păstra meciurile descărcate din API
let currentMatches = [];

// Funcție pentru descarcarea datelor din backend-ul Python (main.py)
async function fetchMatchesFromAPI() {
    try {
        // Preluăm datele de la endpoint-ul FastAPI
        const response = await fetch('/api/matches');
        
        if (!response.ok) {
            throw new Error(`Eroare HTTP! status: ${response.status}`);
        }

        currentMatches = await response.json();
        renderMatches(currentMatches);
    } catch (error) {
        console.error("Eroare la conectarea cu API-ul:", error);
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: #ef4444;">
                    Eroare la încărcarea datelor! Verificați dacă serverul Python rulează și dacă ați introdus corect Cheia API.
                </td>
            </tr>
        `;
    }
}

// Funcție pentru afișarea meciurilor în tabelul HTML
function renderMatches(matches) {
    if (!matches || matches.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: var(--text-muted);">
                    Nu există meciuri disponibile momentan.
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = matches.map(match => {
        const badgeClass = match.confidence === "Mare" ? "badge-high" : "badge-med";

        return `
            <tr>
                <td>${match.datetime}</td>
                <td><strong>${match.homeTeam}</strong> vs <strong>${match.awayTeam}</strong></td>
                <td><span class="odds">${match.odds1}</span></td>
                <td><span class="odds">${match.oddsX}</span></td>
                <td><span class="odds">${match.odds2}</span></td>
                <td><strong>${match.prediction}</strong></td>
                <td><span class="badge ${badgeClass}">${match.confidence}</span></td>
            </tr>
        `;
    }).join("");
}

// Event Listener pentru filtrarea meciurilor după ligă
leagueSelect.addEventListener("change", () => {
    const selectedLeague = leagueSelect.value;
    
    // Actualizăm textul din header
    const selectedOptionText = leagueSelect.options[leagueSelect.selectedIndex].text;
    currentLeagueText.textContent = selectedOptionText;

    if (selectedLeague === "all") {
        renderMatches(currentMatches);
    } else {
        const filtered = currentMatches.filter(match => match.league === selectedLeague);
        renderMatches(filtered);
    }
});

// Încărcăm datele automate din Python imediat ce pagina s-a încărcat
document.addEventListener("DOMContentLoaded", () => {
    fetchMatchesFromAPI();
});
