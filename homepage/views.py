from django.shortcuts import render

# Create your views here.

# howdy/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponse
from django.template.defaultfilters import linebreaksbr
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import *
# from .med_lookup import *
# from .models import MedicationLookup
import time
# from atc_lookup.tasks import send_post_signup_email

# Create your views here.
class HomePageView(TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'homepage/index.html', context=None)