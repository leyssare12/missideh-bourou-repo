class StyledFormMixin:
    """Applique automatiquement les classes Bootstrap aux widgets"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # GARANTIE : Si ui_config n'est pas défini dans la classe enfant, on en crée un vide
        # On s'assure que ui_config est disponible sur l'instance
        # Si la classe a un ui_config, on le prend, sinon dictionnaire vide
        if not hasattr(self, 'ui_config'):
            self.ui_config = getattr(self, 'ui_config', {})

        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ == 'CheckboxInput':
                css_class = 'form-check-input'
            elif field.widget.__class__.__name__ == 'Select':
                css_class = 'form-select shadow-sm'
            else:
                css_class = 'form-control shadow-sm'

            field.widget.attrs.update({'class': css_class})