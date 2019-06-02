from django.contrib.auth import logout
from django.shortcuts import redirect

from .mixins import TemplateAnonymousView


def logout_view(request):
    logout(request)
    return redirect('/')


class LoginErrorView(TemplateAnonymousView):
    template_name = 'user/login_error.html'
