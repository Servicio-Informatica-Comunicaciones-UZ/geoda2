from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
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
    if errors:
        raise Exception("\n".join(errors))
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


@method_decorator(never_cache, name="dispatch")
class LogoutView(LoginRequiredMixin, RedirectView):
    """Log out the current user.

    This view logs out a locally authenticated user,
    or sends a Logout request to the SAML2 Identity Provider.
    """

    url = reverse_lazy(get_config("LOGOUT_REDIRECT_URL"))

    def get(self, request, *args, **kwargs):
        saml_backend = load_backend(
            load_strategy(request), "saml", redirect_uri="/accounts/sls/"
        )
        # As of now, this code only handles the first association.
        association = request.user.social_auth.first()
        if association:
            idp_name = association.uid.split(":")[0]
            sls_url = saml_backend.request_logout(idp_name, association)
            return redirect(sls_url)
        logout(request)
        return super().get(request, *args, **kwargs)


@method_decorator(never_cache, name="dispatch")
class SlsView(View):
    """
    The Single Logout Service processes the Logout response from the Identity Provider.

    The logout request may have been generated by this Service Provider, or other SP.
    """

    url = reverse_lazy(get_config("LOGOUT_REDIRECT_URL"))

    def get(self, request, *args, **kwargs):
        saml_backend = load_backend(
            load_strategy(request), "saml", redirect_uri=str(self.url)
        )
        # As of now, this code only handles the first association.
        association = request.user.social_auth.first()
        idp_name = association.uid.split(":")[0]
        _, errors = saml_backend.process_logout(idp_name, None)

        if errors:
            messages = "\n".join(errors)
            raise Exception(messages)

        logout(request)
        return redirect(str(self.url))
