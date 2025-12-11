$(document).ready(function() {
    // ... votre code existant ...

    $('#confirmDelete').click(function() {
        if (articleToDelete) {
            // Récupère le token CSRF depuis les cookies
            function getCookie(name) {
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    const cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {
                        const cookie = cookies[i].trim();
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
            const csrftoken = getCookie('csrftoken');

            $.ajax({
                url: window.location.pathname,
                method: 'POST',
                data: {
                    id: articleToDelete
                },
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrftoken  // Ajout du token dans les headers
                },
                success: function(response) {
                    if (response.success) {
                        location.reload();
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Erreur:", error);
                    alert("Erreur lors de la suppression: " + xhr.responseText);
                }
            });
        }
        confirmModal.hide();
    });
});