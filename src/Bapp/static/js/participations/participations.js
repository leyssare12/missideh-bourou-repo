document.addEventListener('DOMContentLoaded', function() {
    const select = document.getElementById('contributionType');
    const forms = document.querySelectorAll('.form');

    // Gestionnaire d'événements pour le select
    select.addEventListener('change', function() {
        // Cacher tous les formulaires
        forms.forEach(form => {
            form.classList.add('hidden');
        });

        // Afficher le formulaire sélectionné
        const selectedForm = document.getElementById(this.value);
        if (selectedForm) {
            selectedForm.classList.remove('hidden');
        }
    });

    // Gestionnaire d'événements pour les formulaires
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            console.log('Formulaire soumis :', this.id);
            // Ici, vous pouvez ajouter le code pour traiter les données du formulaire
        });
    });
});