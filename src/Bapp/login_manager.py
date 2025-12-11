# middleware.py
from django.shortcuts import redirect
from django.urls import reverse


class PanelAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Si l'utilisateur n'est pas authentifié et essaie d'accéder à un panel
        if not request.user.is_authenticated:
            if request.path.startswith('/user-panel/') and not request.path.startswith('/user-panel/login/'):
                return redirect('user_login')
            elif request.path.startswith('/manager-panel/') and not request.path.startswith('/manager-panel/login/'):
                return redirect('manager_login')
            elif request.path.startswith('/admin-panel/') and not request.path.startswith('/admin-panel/login/'):
                return redirect('admin_login')

        return None