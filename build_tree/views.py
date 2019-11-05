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
from .build_tree import *
from .models import taskRecord
import time
from .tasks import build_tree_async
import os
from django.shortcuts import redirect
from django.urls import reverse


# Create your views here.
class DownloadFile(UserPassesTestMixin, TemplateView):
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        #return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='HTML tree').exists()
    
    def get(self, request, **kwargs):
        username = None
        if request.user.is_active:
            username = request.user.username
        else:
            username = "NULL"

        template_name = 'build_tree/index.html'

        context = super(DownloadFile, self).get_context_data(**kwargs)
        downloadfileId = int(kwargs.get('downloadfile'))
        taskData = taskRecord.objects.filter(username=username, id=downloadfileId, output_available=True).values()
        #print(taskData[0]['filename'])

        #filename = os.path.dirname(os.path.abspath(__file__))+"/static_files/output/{}".format(taskData[0]['filename'])
        filename = "/webserver/static_files/tree/{}".format(taskData[0]['filename'])
        response = HttpResponse(open(filename, 'rb').read())
        response['Content-Type'] = 'text/plain'
        response['Content-Disposition'] = 'attachment; filename=SnomedTree-{}.html'.format(taskData[0]['conceptFSN'])

        # Set file as not available in database and delete html file
        obj = taskRecord.objects.get(id=downloadfileId)
        obj.output_available = False
        obj.save()

        os.remove(filename)
        return response


class BuildTreeView(UserPassesTestMixin, TemplateView):
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        #return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='HTML tree').exists()
    
    # Handle POST data if present
    def post(self, request, **kwargs):
        if request.method == 'POST':
            # check whether it's valid:
            username = None
            if request.user.is_active:
                username = request.user.username
            else:
                username = "NULL"

            form = SearchForm(request.POST)
            if form.is_valid():
                sctid = str(form.cleaned_data['searchterm'])

                # Get task.id for tracking purposes
                task = build_tree_async.delay(sctid, username)
                task_id = task.id

                return HttpResponseRedirect(reverse('build_tree:index'))

    # if a GET (or any other method) create a blank form
    def get(self, request, **kwargs):
        username = None
        if request.user.is_active:
            username = request.user.username
        else:
            username = "NULL"
        form = SearchForm()
        # Ophalen bestaande taken overnemen van hier boven
        # tasksPerUser = taskRecord.objects.all().order_by("-timestamp")
        totalRunTime = taskRecord.objects.aggregate(Sum('execution_time'))
        try:
            totalRunTime = round(totalRunTime['execution_time__sum'])
        except:
            totalRunTime = "error"
        tasksPerUser = taskRecord.objects.filter(username=username).order_by("-timestamp")
        return render(request, 'build_tree/index.html', {
            'page_title': 'Boomstructuur HTML',
            'form': form,
            'tasksPerUser': tasksPerUser,
            'totalRunTime': totalRunTime,
        })