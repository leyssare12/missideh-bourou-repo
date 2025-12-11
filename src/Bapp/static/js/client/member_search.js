// On recupere la configuration d'urls
const config = document.getElementById('app-config')?.dataset;
// Debug initial

//list vide contenant les identifiants
let allUserIds = [];
let searchTimeout = null;
const DEBOUNCE_DELAY = 300; // Réduit à 300ms

//On recupére ici  tous les identifiants de utilisateurs chargé dans le lien listUrl
//Liste url est le lien vers la vues django chargé de recuperer les identifiants des utilisateurs
document.addEventListener('DOMContentLoaded', function() {
    if (!config.listUrl) return;

    fetch(`${config.listUrl}?get_ids=1`, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Erreur réseau');
        return response.json();
    })
    .then(data => {
        if (data?.ids) {
            allUserIds = data.ids.map(id => String(id).toUpperCase());
        }
    })
    .catch(error => console.error('Erreur:', error));
});

//On recupere le text de la barre de recherche

document.getElementById('filter')?.addEventListener('input', function(e) {
    const searchTerm = e.target.value.trim().toUpperCase();
    const resultsContainer = document.getElementById('searchResults');

    clearTimeout(searchTimeout);

    if (searchTerm.length < 1) {
        if (resultsContainer) resultsContainer.style.display = 'none';
        return;
    }

    searchTimeout = setTimeout(() => {

        //On compare à la liste des identifiants dèjá stockqué dans allUsersIds[]
        // Recherche exacte insensible à la casse
        const foundId = allUserIds.find(id => id === searchTerm);

        if (foundId) {
            const pageNumber = Math.floor(allUserIds.indexOf(foundId) / 10) + 1;
            showResult({
                found: true,
                id: foundId,
                page: pageNumber
            });
        } else {
            performSearch(searchTerm);
        }
    }, DEBOUNCE_DELAY);
});

async function performSearch(searchTerm) {

    try {
        const response = await fetch(`${config.searchUrl}?q=${encodeURIComponent(searchTerm)}`);
        if (!response.ok) throw new Error('Erreur serveur');
        const data = await response.json();
        showResult(data);
    } catch (error) {
        showResult({ found: false });
    }
}
function showResult(data) {
    const name = data.name;
    const page = data.page;
    //on recupere le conteneur des resultats
    const container = document.getElementById('searchResults');
    if (!container) return;

    // Calcul de la position pour éviter le débordement
    const input = document.getElementById('filter');
    const inputRect = input.getBoundingClientRect();


    //on affiche les resultats de recherche
    container.innerHTML = data.found
          ? `<div class="result" tabindex="0">
                 <strong>${name}</strong> - trouvé à la Page: ${data.page}
               </div>`
            : '<div class="no-result">Aucun résultat</div>';

    container.style.display = 'block';

    // Gestion du clic
    const result = container.querySelector('.result');
    if (result) {
        result.style.padding = '10px';
        result.style.top = `${inputRect.bottom}px`;
        result.style.left = `${inputRect.left}px`;
        result.style.color = 'green';

        result.addEventListener('click', () => {
            window.location.href = `?page=${page}`;
        });
           // Effet au survol
        result.addEventListener('mouseover', function() {
            this.style.backgroundColor = '#f5f5f5';
            this.style.cursor = 'pointer';
        });

        // Retour à l'état normal
        result.addEventListener('mouseout', function() {
            this.style.backgroundColor = '';
        });

    }
}

// Fermer les résultats quand on clique ailleurs
document.addEventListener('click', (e) => {
    const container = document.getElementById('searchResults');
    const input = document.getElementById('filter');

    if (container && input &&
        !container.contains(e.target) &&
        e.target !== input) {
        container.style.display = 'none';
    }
});