from django.shortcuts import render, redirect
from django.views.generic import View
from accounts.views import LoginRequiredMixin, AnnonymusRequiredMixin
from django.conf import settings


class LandingView(AnnonymusRequiredMixin, View):
    def get(self, request):
        return render(request, 'pages/landing.html', {
            "TELEGRAM_BOT_USERNAME": settings.TELEGRAM_BOT_USERNAME,
        })


class RegistrationView(View):
    def get(self, request):
        return render(request, 'pages/registration.html')


class LegalNoticeView(AnnonymusRequiredMixin, View):
    authenticated_redirect_url = 'accounts:legal'

    def get(self, request):
        return render(request, 'pages/legal_notice.html')
