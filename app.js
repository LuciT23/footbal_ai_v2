
// Date de test (mock data) pentru meciuri 
const mockMatches = [
    {
        datetime: "30 Iul, 19:30",
        league: "premier-league",
        homeTeam: "Arsenal",
        awayTeam: "Chelsea",
        odds1: "1.85",
        oddsX: "3.60",
        odds2: "4.20",
        prediction: "1 (Vic. Gazde)",
        confidence: "Mare"
    },
    {
        datetime: "30 Iul, 21:45",
        league: "premier-league",
        homeTeam: "Liverpool",
        awayTeam: "Man. City",
        odds1: "2.40",
        oddsX: "3.40",
        odds2: "2.80",
        prediction: "Ambele Marchează",
        confidence: "Medie"
    },
    {
        datetime: "31 Iul, 20:00",
        league: "la-liga",
        homeTeam: "Real Madrid",
        awayTeam: "Sevilla",
        odds1: "1.45",
        oddsX: "4.50",
        odds2: "7.00",
        prediction: "1 & Peste 1.5 goluri",
        confidence: "Mare"
    },
    {
        datetime: "31 Iul, 22:00",
        league: "serie-a",
        homeTeam: "Inter Milan",
        awayTeam: "AC Milan",
        odds1: "2.10",
        oddsX: "3.20",
        odds2: "3.50",
        prediction: "Peste 2.5 goluri",
        confidence: "Medie"
    }
];

// Elemente din DOM
const tableBody = document.getElementById("matches-table-body");
const leagueSelect = document.getElementById("league-select");
const currentLeagueText = document.getElementById("current-league");

// Funcție pentru afișarea meciurilor în tabel
function renderMatches(matches) {
    if (matches.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: var(--text-muted);">
                    Nu există meciuri disponibile pentru această ligă.
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = matches.map(match => {
        // Stabilim clasa pentru stilizarea gradului de încredere
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

// Funcție pentru filtrarea meciurilor după ligă
function filterMatches() {
    const selectedLeague = leagueSelect.value;
    
    // Actualizăm textul din navbar
    const selectedOptionText = leagueSelect.options[leagueSelect.selectedIndex].text;
    currentLeagueText.textContent = selectedOptionText;

    if (selectedLeague === "all") {
        renderMatches(mockMatches);
    } else {
        const filtered = mockMatches.filter(match => match.league === selectedLeague);
        renderMatches(filtered);
    }
}

// Eveniment la schimbarea opțiunii din dropdown
leagueSelect.addEventListener("change", filterMatches);

// Încărcarea inițială a datelor
document.addEventListener("DOMContentLoaded", () => {
    renderMatches(mockMatches);
});

