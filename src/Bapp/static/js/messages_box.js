// static/js/messages.js
document.addEventListener('DOMContentLoaded', function() {
    // Fermer au clic
    document.querySelectorAll('.alert .close').forEach(btn => {
        btn.addEventListener('click', function() {
            this.parentElement.style.animation = 'fadeOut 0.5s forwards';
            setTimeout(() => this.parentElement.remove(), 500);
        });
    });

    // Fermer automatiquement après 5 secondes
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.animation = 'fadeOut 0.5s forwards';
            setTimeout(() => alert.remove(), 500);
        }, 10000);
    });
});