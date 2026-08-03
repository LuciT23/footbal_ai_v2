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
                <td colspan="8" style="text-align: center; color: #ef4444;">
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
                <td colspan="8" style="text-align: center; color: var(--text-muted);">
                    Nu există meciuri disponibile momentan.
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = matches.map(match => {
        const badgeClass = match.confidence === "Mare" ? "badge-high" : "badge-med";

        // Escapăm numele echipelor pentru a evita erori la transmiterea în funcție
        const homeEscaped = match.homeTeam.replace(/'/g, "\\'");
        const awayEscaped = match.awayTeam.replace(/'/g, "\\'");

        return `
            <tr style="cursor: pointer;" onclick="openMatchStats('${homeEscaped}', '${awayEscaped}')">
                <td>${match.datetime}</td>
                <td><strong>${match.homeTeam}</strong> vs <strong>${match.awayTeam}</strong></td>
                <td><span class="odds">${match.odds1}</span></td>
                <td><span class="odds">${match.oddsX}</span></td>
                <td><span class="odds">${match.odds2}</span></td>
                <td><strong>${match.prediction}</strong></td>
                <td><span class="badge ${badgeClass}">${match.confidence}</span></td>
                <td>
                    <button class="btn-analytics" onclick="event.stopPropagation(); openMatchStats('${homeEscaped}', '${awayEscaped}')" style="background:#d4af37; color:#000; border:none; padding:4px 8px; border-radius:4px; font-weight:bold; cursor:pointer; font-size:11px;">
                        📊 Stats
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}

// ==============================================================================
// LOGICĂ PENTRU MODALUL DE STATISTICI & ANALYTICS AI (STIL GOLD & DARK)
// ==============================================================================

async function openMatchStats(homeTeam, awayTeam) {
    const modal = document.getElementById('statsModal');
    const title = document.getElementById('modalMatchTitle');
    const container = document.getElementById('probBarsContainer');
    
    // Dacă nu există încă modalul în HTML, îl creăm dinamic
    if (!modal) {
        createModalInDOM();
        return openMatchStats(homeTeam, awayTeam);
    }

    modal.style.display = 'block';
    title.innerText = `${homeTeam} vs ${awayTeam}`;
    container.innerHTML = '<p style="text-align:center; color:#888; padding:20px;">Se încarcă datele și calculele AI...</p>';

    try {
        const response = await fetch(`/api/match-analytics?home=${encodeURIComponent(homeTeam)}&away=${encodeURIComponent(awayTeam)}`);
        const data = await response.json();

        let html = '';
        if (data.overall_probabilities) {
            data.overall_probabilities.forEach(item => {
                html += `
                    <div style="margin-bottom:12px;">
                        <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px; font-weight:600;">
                            <span>${item.label}</span>
                            <span style="color: #d4af37;">${item.val}%</span>
                        </div>
                        <div style="background-color: #222; border-radius: 20px; height: 16px; overflow: hidden;">
                            <div class="bg-${item.color}" style="width: ${item.val}%; height:100%; border-radius: 20px; transition: width 0.5s ease-in-out;"></div>
                        </div>
                    </div>
                `;
            });
        }

        container.innerHTML = html;
    } catch (err) {
        console.error("Eroare preluare statistici:", err);
        container.innerHTML = '<p style="color:#ef4444; text-align:center;">A apărut o eroare la preluarea statisticilor.</p>';
    }
}

function closeStats() {
    const modal = document.getElementById('statsModal');
    if (modal) modal.style.display = 'none';
}

// Funcție ajutătoare care creează modalul în caz că nu există în index.html
function createModalInDOM() {
    const modalHTML = `
        <div id="statsModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); backdrop-filter:blur(4px); z-index:9999; overflow-y:auto; padding:20px 10px;">
            <div style="background:#141414; border:1px solid #2a2a2a; border-radius:14px; padding:20px; max-width:440px; margin:40px auto; box-shadow:0 10px 30px rgba(0,0,0,0.5); color:#fff; font-family:sans-serif;">
                <div style="text-align:right;">
                    <button onclick="closeStats()" style="background:none; border:none; color:#fff; font-size:22px; cursor:pointer;">✕</button>
                </div>
                <h3 id="modalMatchTitle" style="text-align:center; margin-bottom:5px; font-size:18px; color:#fff;">Echipa 1 vs Echipa 2</h3>
                <p style="color:#d4af37; text-transform:uppercase; font-weight:bold; letter-spacing:1px; text-align:center; font-size:11px; margin-bottom:20px;">Statistici & Analytics AI</p>
                <div id="probBarsContainer"></div>
            </div>
        </div>
        <style>
            .bg-green { background: linear-gradient(90deg, #27ae60, #2ecc71); }
            .bg-orange { background: linear-gradient(90deg, #d35400, #e67e22); }
            .bg-red { background: linear-gradient(90deg, #c0392b, #e74c3c); }
        </style>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);
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
