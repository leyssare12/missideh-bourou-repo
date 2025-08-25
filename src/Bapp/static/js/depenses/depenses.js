
$(document).ready(function() {
    const form = $('#depenseForm');
    const messageAlert = $('#message-alert');
    const messageBox = $('#messageBox');
    const searchUrl = $('#depenseForm').data('url');
    console.log(searchUrl);

    function showMessageBox(message) {
        // Mettre à jour le texte
        messageBox.find('.message-box-text').html(message);

        // Réinitialiser les animations
        messageBox.find('.message-box-progress').remove();
        messageBox
            .append('<div class="message-box-progress"></div>')
            .removeClass('hide')
            .addClass('show')
            .show();

        // Programmer la disparition
        setTimeout(() => {
            messageBox.addClass('hide');
            setTimeout(() => {
                messageBox
                    .removeClass('show hide')
                    .hide();
            }, 500);
        }, 5000);
    }

    function clearMessages() {
        messageAlert.hide();
        $('.invalid-feedback').empty().hide();
        $('.depense-input, .depense-textarea').removeClass('is-invalid is-valid');
        $('.field-success').remove();
    }

    function handleSuccess(messages) {
        // Afficher la message box
        if (messages.success.global) {
            showMessageBox(messages.success.global);
        }

        // Messages de succès spécifiques aux champs
        if (messages.success.montant) {
            $('#depense-numberInput')
                .removeClass('is-invalid')
                .addClass('is-valid')
                .after(`<div class="field-success text-success small mt-1">${messages.success.montant}</div>`);
        }

        if (messages.success.motif) {
            $('#depense-textInput')
                .removeClass('is-invalid')
                .addClass('is-valid')
                .after(`<div class="field-success text-success small mt-1">${messages.success.motif}</div>`);
        }

        // Réinitialiser le formulaire après un délai
        setTimeout(() => {
            form[0].reset();
            $('.field-success').fadeOut(300, function() {
                $(this).remove();
            });
            $('.depense-input, .depense-textarea').removeClass('is-valid');
        }, 5000);
    }

    function handleErrors(messages) {
        // Message d'erreur global
        if (messages.errors.global) {
            messageAlert
                .removeClass('alert-success')
                .addClass('alert-danger')
                .html(messages.errors.global)
                .show();
        }

        // Afficher les erreurs spécifiques aux champs
        Object.entries(messages.errors).forEach(([field, errors]) => {
            if (field !== 'global' && errors.length) {
                const input = field === 'montant_depense' ?
                    $('#depense-numberInput') :
                    $('#depense-textInput');

                const errorDiv = $(`#error-${field}`);

                input.addClass('is-invalid');
                errorDiv
                    .html(errors.join('<br>'))
                    .show();
            }
        });
    }

    form.on('submit', function(e) {
        e.preventDefault();
        clearMessages();

        $.ajax({
            url: searchUrl,
            type: 'POST',
            data: form.serialize(),
            dataType: 'json',
            success: function(response) {
                if (response.status) {
                    handleSuccess(response);
                } else {
                    handleErrors(response);
                }
            },
            error: function() {
                messageAlert
                    .removeClass('alert-success')
                    .addClass('alert-danger')
                    .html('Erreur de connexion au serveur. Veuillez réessayer.')
                    .show();
            }
        });
    });

    // Nettoyage des erreurs lors de la saisie
    $('.depense-input, .depense-textarea').on('input', function() {
        const fieldName = $(this).attr('name');
        $(this)
            .removeClass('is-invalid is-valid')
            .siblings('.field-success, .invalid-feedback')
            .hide();
    });
});
