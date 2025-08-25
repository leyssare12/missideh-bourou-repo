/*document.addEventListener('DOMContentLoaded', function() {
  const titleInput = document.querySelector('#id_title');
  const submitBtn = document.querySelector('button[type="submit"]');

  // Auto-focus et limite de caractères
  if (titleInput) {
    titleInput.focus();
    titleInput.addEventListener('input', function() {
      if (this.value.length > 200) {
        this.value = this.value.slice(0, 200);
      }
    });
  }

  // Confirmer avant quitter si modifications non enregistrées
  let formChanged = false;
  document.querySelector('.article-form').addEventListener('change', () => {
    formChanged = true;
  });
  window.addEventListener('beforeunload', (e) => {
    if (formChanged) {
      e.preventDefault();
      e.returnValue = '';
    }
  });
});
*/
$(document).ready(function() {
    // Initialize toast
    const toastEl = document.getElementById('message-toast');
    const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
    console.log("Document chargé avec succés")

    // Form submission handler
    $('#article-form').on('submit', function(e) {
        e.preventDefault();
        const form = $(this);
        const submitBtn = form.find('button[type="submit"]');
        const submitText = submitBtn.find('.submit-text');
        const spinner = submitBtn.find('.spinner-border');

        // Show loading state
        submitText.text('Enregistrement...');
        spinner.removeClass('d-none');
        submitBtn.prop('disabled', true);

        // Reset validation
        form.find('.is-invalid').removeClass('is-invalid');
        form.find('.invalid-feedback').text('');

        // Prepare form data
        const formData = new FormData(this);
        console.log(window.location.pathname);

        $.ajax({
            url: window.location.pathname,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                if (response.success) {
                    showToast(response.success, 'success');
                    // Optional: form[0].reset();
                } else if (response.errors) {
                    handleFormErrors(response.errors);
                }
            },
            error: function(xhr) {
                try {
                    const errResponse = JSON.parse(xhr.responseText);
                    if (errResponse.errors) {
                        handleFormErrors(errResponse.errors);
                    } else {
                        showToast("Erreur serveur inattendue", 'error');
                    }
                } catch (e) {
                    showToast("Erreur de connexion", 'error');
                }
            },
            complete: function() {
                submitText.text('Enregistrer');
                spinner.addClass('d-none');
                submitBtn.prop('disabled', false);
            }
        });
    });

    function showToast(message, type) {
        const toastBody = $('#toast-body');
        const toast = $('#message-toast');

        toastBody.text(message);
        toast.removeClass('success error').addClass(type);
        toast.addClass('show');

        // Hide automatically after 5 seconds
        setTimeout(() => {
            toast.removeClass('show');
        }, 5000);
    }

    function handleFormErrors(errors) {
        if (typeof errors === 'string') {
            showToast(errors, 'error');
            return;
        }

        if (typeof errors === 'object') {
            let hasFieldErrors = false;

            for (const field in errors) {
                if (errors.hasOwnProperty(field)) {
                    const errorMessage = Array.isArray(errors[field]) ?
                        errors[field].join(' ') : errors[field];

                    if (field === '__all__') {
                        showToast(errorMessage, 'error');
                    } else {
                        const input = $(`[name="${field}"]`);
                        input.addClass('is-invalid');
                        $(`#error-${field}`).text(errorMessage);
                        hasFieldErrors = true;
                    }
                }
            }

            if (hasFieldErrors) {
                // Scroll to first error
                $('html, body').animate({
                    scrollTop: $('.is-invalid').first().offset().top - 100
                }, 500);
            }
        }
    }

    // Add animation when page loads
    $('.editorial-card').addClass('animate-form');

    // Better file input display
    $('.form-control-file').on('change', function() {
        const fileName = $(this).val().split('\\').pop();
        $(this).next('.custom-file-label').html(fileName || 'Choisir un fichier');
    });
});