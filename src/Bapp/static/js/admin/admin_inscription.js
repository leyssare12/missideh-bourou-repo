        // Fonctionnalité d'affichage/masquage du mot de passe
        document.getElementById('togglePassword').addEventListener('click', function() {
            const passwordInput = document.getElementById('password');
            const icon = this.querySelector('i');
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.classList.replace('fa-eye', 'fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                icon.classList.replace('fa-eye-slash', 'fa-eye');
            }
        });

        document.getElementById('toggleConfirmPassword').addEventListener('click', function() {
            const confirmPasswordInput = document.getElementById('confirmPassword');
            const icon = this.querySelector('i');
            if (confirmPasswordInput.type === 'password') {
                confirmPasswordInput.type = 'text';
                icon.classList.replace('fa-eye', 'fa-eye-slash');
            } else {
                confirmPasswordInput.type = 'password';
                icon.classList.replace('fa-eye-slash', 'fa-eye');
            }
        });

        // Vérification de la force du mot de passe
        document.getElementById('password').addEventListener('input', function() {
            const password = this.value;
            const strengthBar = document.getElementById('strengthBar');
            let strength = 0;

            if (password.length > 0) strength += 20;
            if (password.length >= 8) strength += 20;
            if (/[A-Z]/.test(password)) strength += 20;
            if (/[0-9]/.test(password)) strength += 20;
            if (/[^A-Za-z0-9]/.test(password)) strength += 20;

            strengthBar.style.width = strength + '%';

            if (strength < 40) {
                strengthBar.style.backgroundColor = '#ff4757';
            } else if (strength < 80) {
                strengthBar.style.backgroundColor = '#ffa502';
            } else {
                strengthBar.style.backgroundColor = '#2ed573';
            }
        });

        // Validation du formulaire
        document.getElementById('registrationForm').addEventListener('submit', function(e) {
            e.preventDefault();

            // Réinitialiser les messages d'erreur
            document.querySelectorAll('.error-message').forEach(el => {
                el.style.display = 'none';
            });

            let isValid = true;

            // Validation des champs
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

            const password = document.getElementById('password').value;
            if (!password || password.length < 8) {
                document.getElementById('passwordError').style.display = 'block';
                isValid = false;
            }

            const confirmPassword = document.getElementById('confirmPassword').value;
            if (password !== confirmPassword) {
                document.getElementById('confirmPasswordError').style.display = 'block';
                isValid = false;
            }

            if (isValid) {
                // Simulation d'envoi réussi
                document.getElementById('successMessage').style.display = 'block';
                this.reset();
                document.getElementById('strengthBar').style.width = '0%';

                // Faire défiler vers le message de succès
                document.getElementById('successMessage').scrollIntoView({ behavior: 'smooth' });
            }
        });