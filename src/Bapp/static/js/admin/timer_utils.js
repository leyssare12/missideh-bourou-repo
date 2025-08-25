        let timeout = 20; // temps maximum d'inactivité en secondes
        let counter = timeout; // compteur initialisé au temps maximum
        const searchUrl = $('#countdownDisplay').data('url');

        console.log(searchUrl)
        const counterElement = document.getElementById('countdownDisplay');
        function resetCounter() {
            counter = timeout; // réinitialise le compteur
        }

        function decrementCounter() {
            counter--; // décrémente le compteur chaque seconde
            counterElement.textContent = counter;
            console.log('Il vous reste: '+counter+' secondes')

            if (counter <= 0) {
                //alert("Vous avez été déconnecté en raison d'une inactivité.");
                // Redirection ou déconnexion
                console.log("'Lurl est: "+searchUrl)
                window.location.href = searchUrl; // ou une autre action

            }
        }

        // Réinitialiser le compteur sur des événements d'interaction
        document.body.addEventListener('mousemove', resetCounter);
        document.body.addEventListener('keydown', resetCounter);
        document.body.addEventListener('click', resetCounter);

        // Décrémenter le compteur chaque seconde
        setInterval(decrementCounter, 1000);