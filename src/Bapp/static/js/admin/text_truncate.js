class TexteTronque {
    constructor(options = {}) {
        this.longueurMax = options.longueurMax || 50;
        this.selector = options.selector || 'td[data-label]';
        this.classeTronquee = 'texte-tronque';
        this.classeActive = 'tooltip-actif';
        this.init();
    }

    init() {
        this.appliquerTroncature();
        this.ajouterEcouteurs();

        window.addEventListener('resize', () => {
            this.appliquerTroncature();
        });
    }

    ajouterEcouteurs() {
        document.addEventListener('click', (e) => {
            // Trouve le conteneur texte-tronque le plus proche
            const conteneurTronque = e.target.closest(`.${this.classeTronquee}`);
            const tousTooltips = document.querySelectorAll(`.${this.classeTronquee}`);

            if (conteneurTronque) {
                // Ferme tous les autres tooltips
                tousTooltips.forEach(tooltip => {
                    if (tooltip !== conteneurTronque) {
                        tooltip.classList.remove(this.classeActive);
                    }
                });
                // Toggle le tooltip cliqué
                conteneurTronque.classList.toggle(this.classeActive);
                e.stopPropagation();
            } else {
                // Ferme tous les tooltips si on clique ailleurs
                tousTooltips.forEach(tooltip => {
                    tooltip.classList.remove(this.classeActive);
                });
            }
        });
    }

    tronquerTexte(texte) {
        if (texte.length <= this.longueurMax) return texte;
        return texte.substring(0, this.longueurMax) + '...';
    }

    appliquerTroncature() {
        const cellules = document.querySelectorAll(this.selector);

        cellules.forEach(cellule => {
            let conteneur = cellule.querySelector(`.${this.classeTronquee}`);
            const texteOriginal = conteneur ? conteneur.getAttribute('data-texte-complet') : cellule.textContent.trim();

            if (window.innerWidth <= 780) {
                if (!conteneur) {
                    // Créer le conteneur principal
                    conteneur = document.createElement('div');
                    conteneur.className = this.classeTronquee;
                    conteneur.setAttribute('data-texte-complet', texteOriginal);

                    // Créer le span pour le texte visible
                    const texteVisible = document.createElement('span');
                    texteVisible.className = 'texte-visible';
                    texteVisible.textContent = this.tronquerTexte(texteOriginal);

                    // Créer le tooltip
                    const tooltipContent = document.createElement('div');
                    tooltipContent.className = 'tooltip-content';
                    tooltipContent.textContent = texteOriginal;

                    // Ajouter le bouton de fermeture au tooltip
                    const fermer = document.createElement('span');
                    fermer.className = 'fermer';
                    fermer.textContent = '×';
                    fermer.onclick = (e) => {
                        e.stopPropagation();
                        conteneur.classList.remove(this.classeActive);
                    };

                    tooltipContent.appendChild(fermer);
                    conteneur.appendChild(texteVisible);
                    conteneur.appendChild(tooltipContent);

                    cellule.textContent = '';
                    cellule.appendChild(conteneur);
                } else {
                    // Mise à jour du texte visible si le conteneur existe déjà
                    const texteVisible = conteneur.querySelector('.texte-visible');
                    if (texteVisible) {
                        texteVisible.textContent = this.tronquerTexte(texteOriginal);
                    }
                }
            } else {
                // Mode desktop : restaurer le texte original
                if (conteneur) {
                    cellule.textContent = texteOriginal;
                }
            }
        });
    }
}