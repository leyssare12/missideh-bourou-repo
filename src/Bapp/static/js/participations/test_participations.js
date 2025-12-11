// chargement du DOM

$(document).ready(function() {
    // Récupération de l'URL de recherche
    const searchUrl = $('#userSearchBlock').data('url');
    if (!searchUrl) {
        console.error("L'URL de recherche n'est pas définie dans data-url");
    }

    console.log("URL de recherche:", searchUrl);

    // Définition des sélecteurs et variables
    let formErrors = {}; // Stocke les erreurs transmises depuis Django
    const selectors = {
        userTypeSelect: '#userType',
        userSearchBlock: '#userSearchBlock',
        userSearchInput: '#id_search_term',
        userInfo: '#userInfo',
        formContainers: '.form-container',
        userPrenom: '#userPrenom',
        userIdentifiant: '#userIdentifiant',
        participationForms: '.participation-form',
        // Ajout du sélecteur pour les résultats de recherche
        searchResults: '#searchResults',
        successMessage: ".form-messages",
    };

    $(selectors.successMessage).hide();
    const state = {
        selectedUserId: null,
        isSubmitting: false
    };

    // Fonction pour créer un élément de la liste des résultats
    function createUserListItem(user) {
        return `
            <div class="search-result-item" data-user-id="${user.id}">
                <div class="user-info">
                    <span class="prenom">${user.prenom}</span>
                    <span class="identifiant">${user.identifiant}</span>
                </div>
            </div>
        `;
    }

    // Fonction pour gérer la sélection d'un utilisateur
    function handleUserSelection(user) {
        state.selectedUserId = user.id;

        // Mise à jour de l'affichage des informations utilisateur
        $(selectors.userPrenom).text(`${user.prenom}`);
        $(selectors.userIdentifiant).text(`${user.identifiant}`);
        $(selectors.userInfo).show();

        // Affichage du formulaire correspondant
        const selectedType = $(selectors.userTypeSelect).val();
        $(`#${selectedType}Form`).show();
        $(`#${selectedType}Id`).val(user.id);

        // Masquer les résultats de recherche
        $(selectors.searchResults).removeClass('active');

        console.log("Utilisateur sélectionné:", user);
    }

    // Gestion du changement de type d'utilisateur
    $(selectors.userTypeSelect).on('change', function() {
        const selectedType = $(this).val();
        console.log("Type d'utilisateur sélectionné:", selectedType);

        // Cacher tous les formulaires
        $(selectors.formContainers).hide();
        $(selectors.userSearchBlock).hide();

        if (selectedType === 'user1' || selectedType === 'user2') {
            $(selectors.userSearchBlock).show();
            $(`#${selectedType}Form`).hide();
            $(selectors.userInfo).hide();
        } else if (selectedType === 'user3') {
            $('#user3Form').show();
        }
    });

    // Système de recherche d'utilisateur avec affichage des résultats
    let searchTimeout;
    $(selectors.userSearchInput).on('input', function() {
        const searchTerm = $(this).val().trim();
        console.log("Terme de recherche:", searchTerm);

        // Annuler la recherche précédente
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }

        // Si le champ est vide, masquer les résultats
        if (searchTerm.length === 0) {
            $(selectors.searchResults).removeClass('active').empty();
            $(selectors.userInfo).hide();
            return;
        }

        // Vérifier la longueur minimale
        if (searchTerm.length < 2) {
            console.log("Terme de recherche trop court");
            $(selectors.userInfo).hide();
            return;
        }

        // Définir le nouveau timeout
        searchTimeout = setTimeout(() => {
            console.log("Envoi de la requête de recherche...");

            $.ajax({
                url: searchUrl,
                method: 'GET',
                data: { term: searchTerm },
                beforeSend: function() {
                    console.log("Début de la requête AJAX");
                },
                success: function(data) {
                    console.log("Réponse reçue:", data);

                    if (data.status === 'success' && data.results.length > 0) {
                        // Construire et afficher la liste des résultats
                        const resultsHtml = data.results
                            .map(user => createUserListItem(user))
                            .join('');

                        $(selectors.searchResults)
                            .html(resultsHtml)
                            .addClass('active');
                    } else {
                        // Afficher un message si aucun résultat
                        $(selectors.searchResults)
                            .html('<div class="search-result-item">Aucun résultat trouvé</div>')
                            .addClass('active');
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Erreur lors de la recherche:", error);
                    $(selectors.searchResults)
                        .html('<div class="search-result-item">Une erreur est survenue</div>')
                        .addClass('active');
                }
            });
        }, 300);
    });
    //Generation d'un message d'erreurs quand le champs ne remplie pas les conditions requise
    $(`${selectors.participationForms} input, ${selectors.participationForms} textarea`).on('blur', function () {
          const $field = $(this);
          const fieldName = $field.attr('name'); // nom du champ pour trouver l'erreur
          console.log("Le nom d'attribut est: "+fieldName);
          if (!$field.next('.field-error').length) {
            $field.after('<div class="field-error" style="display:none; color:red;"></div>');
          }

          const $errorBox = $field.next('.field-error');

          // Si erreur serveur enregistrée pour ce champ
          /*
          if (formErrors[fieldName]) {
            const errorMessage = formErrors[fieldName][0].message; // Django envoie un tableau d'erreurs
            console.log(errorMessage);
            $field.addClass('input-error');
            $errorBox.text(errorMessage).fadeIn();
          } else if (!this.checkValidity()) {
            // fallback sur validation native HTML5
            $field.addClass('input-error');
            $field.css({
                'border':'1px solid red',
                'background-color': '#ffe6e6'
            });
            $errorBox.text(this.validationMessage).fadeIn();
          } else {
            $field.removeClass('input-error');
            $errorBox.fadeOut();
          }*/
        });


    // Gestion des clics sur les résultats de recherche
    $(document).on('click', '.search-result-item', function() {
        const userId = $(this).data('user-id');
        const userPrenom = $(this).find('.prenom').text();
        const userIdentifiant = $(this).find('.identifiant').text();

        handleUserSelection({
            id: userId,
            prenom: userPrenom,
            identifiant: userIdentifiant
        });
    });

    // Fermeture de la liste des résultats au clic extérieur
    $(document).on('click', function(event) {
        if (!$(event.target).closest('#userSearchBlock').length) {
            $(selectors.searchResults).removeClass('active');
        }
    });

    // Navigation au clavier dans les résultats
    $(selectors.userSearchInput).on('keydown', function(e) {
        const results = $('.search-result-item');
        const current = $('.search-result-item.selected');

        switch(e.keyCode) {
            case 40: // Flèche bas
                e.preventDefault();
                if (current.length === 0) {
                    results.first().addClass('selected');
                } else {
                    current.removeClass('selected')
                           .next('.search-result-item')
                           .addClass('selected');
                }
                break;

            case 38: // Flèche haut
                e.preventDefault();
                if (current.length === 0) {
                    results.last().addClass('selected');
                } else {
                    current.removeClass('selected')
                           .prev('.search-result-item')
                           .addClass('selected');
                }
                break;

            case 13: // Entrée
                e.preventDefault();
                if (current.length) {
                    current.click();
                }
                break;
        }
    });

    // Gestion de la soumission du formulaire
    $(selectors.participationForms).on('submit', function(e) {
    e.preventDefault();

    const $form = $(this);
    const url = $form.data('url');
    const $form_selectors = $form.closest(".form-container");
    const $messageBox = $form_selectors.find(".form-messages");
    const $fieldErrors = $form_selectors.find(".field-errors");
    console.log($form_selectors, $messageBox, $fieldErrors)
    // Empêche la double soumission
    if (state.isSubmitting) {
        console.log("Soumission déjà en cours");
        return;
    }

    state.isSubmitting = true;

    // Nettoyage ancien contenu
    $messageBox.html('').hide();
    $fieldErrors.html('');

    const formData = new FormData(this);

    $.ajax({
        url: url,
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            if (response.status === 'success') {
                $messageBox
                    .html(`<div class="messageBox">${response.message}</div>`)
                    .fadeIn();
                console.log(response.message)
                // Disparition du message après 3s
                setTimeout(() => {
                    $messageBox.fadeOut();
                }, 4000);

                $form[0].reset();  // Réinitialise le formulaire
            } else {
                if (response.errors) {
                    for (const field in response.errors) {
                        const messages = response.errors[field];
                        messages.forEach(msgObj => {
                            // Affiche chaque message dans la div field-errors
                            console.log(msgObj)
                            $fieldErrors.append(
                                `<p class="text-sm text-red-600" style="color:red; text-align:center;">${field !== '__all__' ? `<strong>Erreur: ${field}</strong>: ` : ''}${msgObj.message}</p>`
                            );
                        });
                    }

                    $messageBox
                        .html(`<div class="alert alert-danger" style="display:block;">Veuillez corriger les erreurs du formulaire.</div>`)
                        .fadeIn();
                    console.log('Le messageBox: '+$messageBox.length);
                    console.log(response.errors)
                    formErrors = response.errors; // <-- On enregistre ici les erreurs
                    // En cas d'erreurs on cache le div contenant le message success
                    $($messageBox).hide();
                    console.log('Le messageBox: '+$messageBox.length);
                }
                else{
                    formErrors = {}; // Reset en cas de succès
                }
            }
        },
        error: function(xhr, status, error) {
            console.error("Erreur AJAX:", error);
            $messageBox
                .html(`<div class="alert alert-danger">Une erreur est survenue lors de la soumission.</div>`)
                .fadeIn();
        },
        complete: function() {
            state.isSubmitting = false;
        }
    });
});

});