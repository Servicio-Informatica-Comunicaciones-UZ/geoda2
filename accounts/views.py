from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic.base import RedirectView, View


from annoying.functions import get_config
from social_django.utils import load_backend, load_strategy


def metadata_xml(request):
    """Muestra los metadatos para el Proveedor de Identidad (IdP) de SAML."""
    complete_url = reverse("social:complete", args=("saml",))
    saml_backend = load_backend(
        load_strategy(request), "saml", redirect_uri=complete_url
    )
    metadata, errors = saml_backend.generate_metadata_xml()
    if not errors:
        return HttpResponse(content=metadata, content_type="text/xml")


class UserdataView(LoginRequiredMixin, View):
    """Muestra los datos del usuario."""

    def get(self, request, *args, **kwargs):
        context = {}
        context["datos_usuario"] = {
            field.name: field.value_to_string(request.user)
            for field in request.user._meta.fields
        }
        return render(request, "registration/userdata.html", context=context)


class LogoutView(LoginRequiredMixin, RedirectView):
    url = reverse_lazy(get_config("LOGOUT_REDIRECT_URL"))

    def get(self, request, *args, **kwargs):
        # TODO Desconectar de SAML
        logout(request)
        return super().get(request, *args, **kwargs)
