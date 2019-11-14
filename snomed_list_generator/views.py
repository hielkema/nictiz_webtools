from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponse
from django.template.defaultfilters import linebreaksbr
from django.utils.http import urlquote
from django.db.models import Sum
from .forms import *
from django.contrib.auth import *
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from celery.result import AsyncResult
from .models import *
import time
from .tasks import *
import os
from django.shortcuts import redirect
from django.urls import reverse


# Create your views here.
class DownloadFile(UserPassesTestMixin, TemplateView):
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        #return self.request.user.has_perm('Build_Tree.make_taskRecordBuildFlat')
        return self.request.user.groups.filter(name='HTML tree').exists()
    
    def get(self, request, **kwargs):
        username = None
        if request.user.is_active:
            username = request.user.username
        else:
            username = "NULL"

        template_name = 'build_tree_excel/index.html'

        context = super(DownloadFile, self).get_context_data(**kwargs)
        downloadfileId = int(kwargs.get('downloadfile'))
        taskData = taskRecordBuildFlat.objects.filter(username=username, id=downloadfileId, output_available=True).values()
        #print(taskData[0]['filename'])

        #filename = os.path.dirname(os.path.abspath(__file__))+"/static_files/output/{}".format(taskData[0]['filename'])
        filename = "/webserver/static_files/tree/{}".format(taskData[0]['filename'])
        response = HttpResponse(open(filename, 'rb').read())
        response['Content-Type'] = 'text/plain'
        response['Content-Disposition'] = 'attachment; filename=SnomedTree-{}.xlsx'.format(taskData[0]['conceptFSN'])

        # Set file as not available in database and delete html file
        obj = taskRecordBuildFlat.objects.get(id=downloadfileId)
        obj.output_available = False
        obj.save()

        os.remove(filename)
        return response


class createTaskPageView(UserPassesTestMixin, TemplateView):
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        #return self.request.user.has_perm('Build_Tree.make_taskRecordBuildFlat')
        return self.request.user.groups.filter(name='HTML tree').exists()

    # if a GET (or any other method) create a blank form
    def get(self, request, **kwargs):
        username = request.user.username
        
        form = SearchForm()
        # Ophalen bestaande taken overnemen van hier boven
        # tasksPerUser = taskRecordBuildFlat.objects.all().order_by("-timestamp")
        totalRunTime = snomedListGeneratorLog.objects.aggregate(Sum('execution_time'))
        try:
            totalRunTime = round(totalRunTime['execution_time__sum'])
        except:
            totalRunTime = "error"
        tasksPerUser = snomedListGeneratorLog.objects.filter(username=username).order_by("-timestamp")
        return render(request, 'snomed_list_generator/index.html', {
            'page_title': 'Snomed lijstgenerator',
            'form': form,
            'tasksPerUser': tasksPerUser,
            'totalRunTime': totalRunTime,
        })

class ajaxCreateTask(UserPassesTestMixin, TemplateView):
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        #return self.request.user.has_perm('Build_Tree.make_taskRecordBuildFlat')
        return self.request.user.groups.filter(name='HTML tree').exists()
    
    # Handle POST data if present
    def post(self, request, **kwargs):
        if request.method == 'POST':
            username = request.user.username

            form = SearchForm(request.POST)
            if form.is_valid():
                query = str(form.cleaned_data['query'])
                list_type = str(form.cleaned_data['list_type'])

                print(query, list_type)
                # Get task.id for tracking purposes
                task = snomed_list_generator_excel_v01.delay(query, username)
                task_id = task.id
                print(task_id)
            else:
                print("not valid")
            return HttpResponseRedirect(reverse('snomed_list:index'))

class showTaskPageView(UserPassesTestMixin, TemplateView):
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        #return self.request.user.has_perm('Build_Tree.make_taskRecordBuildFlat')
        return self.request.user.groups.filter(name='HTML tree').exists()
    
    # if a GET (or any other method) create a blank form
    def get(self, request, **kwargs):
        username = request.user.username
        
        form = SearchForm()
        # Ophalen bestaande taken overnemen van hier boven
        # tasksPerUser = taskRecordBuildFlat.objects.all().order_by("-timestamp")
        totalRunTime = snomedListGeneratorLog.objects.aggregate(Sum('execution_time'))
        try:
            totalRunTime = round(totalRunTime['execution_time__sum'])
        except:
            totalRunTime = "error"
        tasksPerUser = snomedListGeneratorLog.objects.filter(username=username).order_by("-timestamp")
        return render(request, 'snomed_list_generator/task_list.html', {
            'page_title': 'Snomed lijstgenerator',
            'form': form,
            'tasksPerUser': tasksPerUser,
            'totalRunTime': totalRunTime,
        })