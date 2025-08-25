
// Attend que le DOM soit complètement chargé avant d'exécuter le code
document.addEventListener('DOMContentLoaded', () => {
    // Récupération des références aux éléments du DOM
    const typeSelect = document.getElementById('type_select');
    const searchForm = document.getElementById('search_form');
    const searchInput = document.getElementById('search_input');
    const searchResults = document.getElementById('search_results');
    const participationForm = document.getElementById('participation_form_container');
    const form_container = document.getElementById('participation_form_container');
    const userIdField = document.getElementById('user_id');
    const typeField = document.getElementById('participation_type');
    const errorMessage = document.getElementById('error_message');


    // Récupération des URLs depuis les attributs data-* des éléments
    const searchUrl = searchInput.dataset.url;
    const submitUrl = form_container.dataset.url;



    //Fonction de chargement de formulaire
    function loadForm(type) {
    fetch(`${submitUrl}?type=${type}`)
        .then(response => response.text())
        .then(html => {
            const container = document.getElementById("participation_form_container");
            container.innerHTML = html;
            container.style.display = "block";
            document.getElementById("participation_type").value = type;
        })
        .catch(error => console.error("Erreur lors du chargement du formulaire :", error));
}


    // Gestion du changement de type de participation
    typeSelect.addEventListener('change', () => {
    const selectedType = typeSelect.value;
    loadForm(selectedType);
});


    //typeSelect.addEventListener('change', () => {
     //   if (typeSelect.value) {
      //      // Affiche le formulaire de recherche si un type est sélectionné
        //    searchForm.style.display = 'block';
       //     typeField.value = typeSelect.value;
       // } else {
            // Cache les formulaires si aucun type n'est sélectionné
     //       searchForm.style.display = 'none';
      //      participationForm.style.display = 'none';
      //  }
    //});

    // Gestion de la recherche en temps réel
    searchInput.addEventListener('input', () => {
        const query = searchInput.value;
        // Ne déclenche la recherche que si au moins 2 caractères sont saisis
        if (query.length < 2) return;

        // Appel API pour la recherche
        //Passer l'url dynamique à fetch
        fetch(`${searchUrl}?recherche=${query}`)
            .then(response => response.json())
            .then(data => {
                // Vide les résultats précédents
                searchResults.innerHTML = '';
                if (data.results) {
                    // Création dynamique des éléments de résultats
                    data.results.forEach(user => {
                        const li = document.createElement('li');
                        li.textContent = user.name;
                        li.style.cursor = 'pointer';
                        // Gestion du clic sur un résultat
                        li.onclick = () => {
                            userIdField.value = user.id;
                            participationForm.style.display = 'block';
                            searchResults.innerHTML = '';
                            searchInput.value = user.name;
                            errorMessage.innerText = '';
                        };
                        searchResults.appendChild(li);
                    });
                }
            })
            .catch(err => {
                errorMessage.innerText = "Erreur lors de la recherche.";
            });
    });

    // Gestion de la soumission du formulaire
    form.addEventListener('submit', function (e) {
        e.preventDefault(); // Empêche la soumission normale du formulaire
        const form = document.getElementById("participation_form");
        const formData = new FormData(form);

        // Envoi des données au serveur
        fetch(submitUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value },
            body: formData
        })
        .then(res => res.json().then(data => ({ status: res.status, data })))
        .then(({ status, data }) => {
            if (status === 200 && data.success) {
                // Gestion du succès
                alert("Participation enregistrée !");
                form.reset();
                participationForm.style.display = 'none';
                searchForm.style.display = 'none';
                typeSelect.value = '';
                errorMessage.innerText = '';
            } else {
                // Gestion des erreurs retournées par le serveur
                const errors = data.errors || { error: "Erreur inconnue." };
                errorMessage.innerText = Object.values(errors).flat().join("\n");
            }
        })
        .catch(() => {
            errorMessage.innerText = "Erreur lors de l'envoi du formulaire.";
        });
    });
});