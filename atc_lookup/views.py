from django.shortcuts import render

# Create your views here.

# howdy/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponse
from django.template.defaultfilters import linebreaksbr
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import *
from .med_lookup import *
from .models import MedicationLookup
import time
from django.shortcuts import redirect
from atc_lookup.tasks import send_post_signup_email

# Create your views here.
class IndexPageView(LoginRequiredMixin, TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'index/index.html', context=None)


# Create your views here.
class AboutPageView(LoginRequiredMixin, TemplateView):
    def get(self, request, **kwargs):
        return render(request, 'about.html', context=None)



# Create your views here.
class MedicinPageView(UserPassesTestMixin, TemplateView):
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        #return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='ATC lookup').exists()
    
    def post(self, request, **kwargs):
        # if this is a POST request we need to process the form data
        if request.method == 'POST':
            # create a form instance and populate it with data from the request:
            form = MedicinSearchForm(request.POST)
            # check whether it's valid:
            if form.is_valid():
                start = time.time()
                output = med_lookup(form.cleaned_data['searchterm'])
                try:
                    print(output[1])
                    error=False
                except KeyError:
                    error="Geen resultaten gevonden"
                #output = linebreaksbr(output)
                # print(os.path.dirname(os.path.abspath(__file__)))
                # output = form.cleaned_data['searchterm']
                # return HttpResponse(output)
                # return HttpResponseRedirect('/thanks/')
                #DB updaten
                username = None
                if request.user.is_active:
                    username = request.user.username
                MedicationLookup.username = username
                stop = time.time()

                lookupData = MedicationLookup.objects.create(username=username, searchterm=form.cleaned_data['searchterm'], execution_time=round(stop-start,1))
                lookupData.save()

                # Print all performed searches
                #search_list = MedicationLookup.objects.all()
                #print(search_list)

                # Print laatste vijf zoekopdrachten
                #searchHistory = MedicationLookup.objects.all().values_list('id','username', 'searchterm', 'execution_time').order_by("-timestamp")[0:5]
                # searchHistory = MedicationLookup.objects.all().order_by("-timestamp")[0:5]
                # for value in searchHistory:
                #     print("ID{} * \"{}\" gezocht * door {}, executietijd [{}]seconden.".format(value.id, value.searchterm, value.username, value.execution_time))
                #print(searchHistory)

                # send_post_signup_email.delay(form.cleaned_data['searchterm'])

                return render(request, 'medicatie/medicatie.html', {
                    'page_title': 'Medicatie opzoeken',
                    'form': form,
                    'respons': output,
                    'error' : error,
                    #'alertbox': searchHistory,
                })
        # if a GET (or any other method) we'll create a blank form
    def get(self, request, **kwargs):
        form = MedicinSearchForm()
        return render(request, 'medicatie/medicatie.html', {'page_title': 'Medicatie opzoeken', 'form': form})