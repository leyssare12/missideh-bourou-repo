

        document.getElementById('registrationForm').addEventListener('submit', function(e) {
            e.preventDefault();

            // Réinitialiser les messages d'erreur
            document.querySelectorAll('.error-message').forEach(el => {
                el.style.display = 'none';
            });

            let isValid = true;

            // Validation simple
            if (!document.getElementById('lastName').value) {
                document.getElementById('lastNameError').style.display = 'block';
                isValid = false;
            }

            if (!document.getElementById('firstName').value) {
                document.getElementById('firstNameError').style.display = 'block';
                isValid = false;
            }

            if (!document.getElementById('country').value) {
                document.getElementById('countryError').style.display = 'block';
                isValid = false;
            }

            const email = document.getElementById('email').value;
            if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                document.getElementById('emailError').style.display = 'block';
                isValid = false;
            }

            const phone = document.getElementById('phone').value;
            if (!phone || !/^[\d\s+-]{10,}$/.test(phone)) {
                document.getElementById('phoneError').style.display = 'block';
                isValid = false;
            }

            if (isValid) {
                // Simulation d'envoi réussi
                document.getElementById('successMessage').style.display = 'block';
                this.reset();

                // Faire défiler vers le message de succès
                document.getElementById('successMessage').scrollIntoView({ behavior: 'smooth' });

                // Envoyer les données au serveur dans une application réelle
                // const formData = new FormData(this);
                // fetch('/api/register', { method: 'POST', body: formData })
                //     .then(response => response.json())
                //     .then(data => console.log(data));
            }
        });
