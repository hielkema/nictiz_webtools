from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.template.defaultfilters import linebreaksbr
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.forms import formset_factory
from django.urls import reverse
from django.db.models import Q
from datetime import datetime
from .forms import *
from .models import *
from pandas import read_excel
import environ
import time
import random
import json
import urllib.request
# Get latest snowstorm client once on startup. Set master or develop
branch = "develop"
url = 'https://raw.githubusercontent.com/mertenssander/python_snowstorm_client/' + \
    branch+'/snowstorm_client.py'
urllib.request.urlretrieve(url, 'snowstorm_client.py')
from snowstorm_client import Snowstorm
from .tasks import *

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))

# Create your views here.
class AjaxTargetSearch(UserPassesTestMixin,TemplateView):
    '''
    Class used for delivering search results when looking for a component to map to.
    Only accessible with edit mapping rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # User has no reason being here if he has no mapping rights
        return self.request.user.groups.filter(name='mapping | edit mapping').exists()
    
    def get(self, request, **kwargs):
        # TODO - Check if project and task exist, otherwise -> redirect to project or homepage.
        search_query = str(request.GET.get('term'))
        print(search_query)

        # Prepare results for select2 AJAX request
        items =[]

        # Start with the best matches: single word postgres match
        snomedComponents = MappingCodesystemComponent.objects.filter(
            Q(component_id__icontains=search_query) |
            Q(component_title__icontains=search_query)
        )
        for component in snomedComponents:
            items.append({
                'id' : component.id, # Intern ID van component -> value van item in dropbox
                'text' : component.component_title, # Bovenste regel
                'codesystem' : component.codesystem_id.codesystem_title + ' ' + component.codesystem_id.codesystem_version,  # Middelste regel
                'comp_id' : component.component_id, # ID in terminologiestelsel, onderste regel
            })
        
        # In addition, full text search if needed
        if len(items) == 0:
            snomedComponents = MappingCodesystemComponent.objects.annotate(search=SearchVector('component_title','component_id',),).filter(search=search_query)        
            for component in snomedComponents:
                items.append({
                    'id' : component.id, # Intern ID van component -> value van item in dropbox
                    'text' : component.component_title, # Bovenste regel
                    'codesystem' : component.codesystem_id.codesystem_title + ' ' + component.codesystem_id.codesystem_version,  # Middelste regel
                    'comp_id' : component.component_id, # ID in terminologiestelsel, onderste regel
                })
        
        # Return Json response
        return JsonResponse({'items':items[:100]})

class AjaxSearchTaskPageView(UserPassesTestMixin,TemplateView):
    '''
    Class used to serve results for searching a specific task from the task manager.
    Only accessible with view tasks rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        return self.request.user.groups.filter(name='mapping | view tasks').exists()
    
    def get(self, request, **kwargs):
        project = int(kwargs.get('project'))
        search_query = str(request.GET.get('term'))
        print(project, search_query)

        if request.GET.get('task_id'):
            task = MappingTask.objects.get(
                    id=int(request.GET.get('task_id')),
                )
            return HttpResponseRedirect(reverse('mapping:index')+'project/'+str(project)+'/task/'+str(task.id))
        else:
            # Prepare results for select2 AJAX request
            items =[]
            # Start with the best matches: single word postgres match
            snomedComponents = MappingCodesystemComponent.objects.filter(
                Q(component_id__icontains=search_query) |
                Q(component_title__icontains=search_query)
            )
            for component in snomedComponents:
                tasks = MappingTask.objects.filter(
                    source_component=component,
                    project_id_id=project,
                )
                for task in tasks:            
                    items.append({
                        'id' : task.id, # Intern ID van component -> value van item in dropbox
                        'text' : component.component_title, # Bovenste regel
                        'codesystem' : component.codesystem_id.codesystem_title + ' ' + component.codesystem_id.codesystem_version,  # Middelste regel
                        'comp_id' : component.component_id, # ID in terminologiestelsel, onderste regel
                    })
            
            return JsonResponse({'items':items[:20]})

class AjaxProgressRecordPageView(UserPassesTestMixin, TemplateView):
    '''
    Class used to save progress on all tasks on a daily basis, called from a cronjob.
    Only accessible with the right cronjob_secret, as set in .env.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        print(self.kwargs['secret'], env('cronjob_secret'))
        if self.kwargs['secret'] == env('cronjob_secret'):
            return True
        else:
            return False

    
    # TODO - daily chronjob to this endpoint / OR get celery beat working
    def get(self, request, **kwargs):
        # Taken per status
        project_list = MappingProject.objects.filter(active=True)
        results = []
        tasks_per_user_dict = []
        tasks_per_status_dict = []

        for project in project_list:        
            try:
                project_list = MappingProject.objects.filter(active=True)
                current_project = MappingProject.objects.get(id=project.id, active=True)
                
                status_list = MappingTaskStatus.objects.filter(project_id=project.id).order_by('status_id')#.exclude(id=current_project.status_complete.id)
                tasks_per_status_labels = []
                tasks_per_status_values = []
                tasks_per_status_dict = []
                user_list = User.objects.filter()
                tasks_per_user_labels = []
                tasks_per_user_values = []
                tasks_per_user_dict = []
                for user in user_list:
                    num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, user=user).exclude(status=current_project.status_complete).count()
                    if num_tasks > 0:
                        num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, user=user).exclude(status=current_project.status_complete).count()
                        tasks_per_user_labels.append(user.username)
                        tasks_per_user_values.append(num_tasks)
                        tasks_per_user_dict.append({
                        'user' : user.username,
                        'num_tasks' : num_tasks,
                        })
                for status in status_list:            
                    num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, status_id=status).count()
                    tasks_per_status_labels.append(status.status_title)
                    tasks_per_status_values.append(num_tasks)
                    tasks_per_status_dict.append({
                        'status' : status.status_title,
                        'num_tasks' : num_tasks,
                        })
            except:
                tasks_per_status_labels = []
                tasks_per_status_values = []
                tasks_per_user_labels = []
                tasks_per_user_values = []
            
            # print(tasks_per_user_dict)
            # print(tasks_per_status_dict)
            try:
                MappingProgressRecord.objects.create(
                    name = 'TasksPerStatus',
                    project = project,
                    labels = '',
                    values = json.dumps(tasks_per_status_dict)
                )
            except Exception as e:
                print(e)
            try:
                MappingProgressRecord.objects.create(
                    name = 'TasksPerUser',
                    project = project,
                    labels = '',
                    values = json.dumps(tasks_per_user_dict)
                )
            except Exception as e:
                print(e)
            
        try:
            return JsonResponse({
            'project' : project.id,
            'results' : tasks_per_status_dict,
            })
        except Exception as e:
            print(e)
            return redirect('login')

class TaskCreatePageView(UserPassesTestMixin,TemplateView):
    '''
    Class for creating tasks pageview.
    Only accessible with create tasks permissions.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        return self.request.user.groups.filter(name='mapping | create tasks').exists()
    def post(self, request, **kwargs):
        form = TaskCreateForm(request.POST)
        handled = {}
        if form.is_valid():
            project = MappingProject.objects.get(id=int(form.cleaned_data['project']))
            codesystem = MappingCodesystem.objects.get(id=int(form.cleaned_data['codesystem']))
            # user = User.objects.get(id=request.user.id) # Taken maken we nu altijd zonder gebruiker

            status1 = MappingTaskStatus.objects.get(project_id = form.cleaned_data['project'], status_id = 1)
   
            projects = MappingProject.objects.all()
            project_list = []
            for project in projects:
                project_list.append((project.id, project.title))

            if request.POST.get('type') == "Taak maken voor alle componenten":
                tasks_list = []
                components_in_syst = MappingCodesystemComponent.objects.filter(codesystem_id = codesystem)
                for component in components_in_syst:
                    tasks_list.append(component.component_id)
            else:
                tasks_list = form.cleaned_data['tasks'].splitlines()

            
            for component in tasks_list:
                print("\nAttempting to find component ",component)
                try:
                    component_obj = MappingCodesystemComponent.objects.get(component_id=component, codesystem_id=codesystem)
                    print("Component found: ", component_obj)

                    obj, created = MappingTask.objects.get_or_create(
                        project_id=project,
                        source_component=component_obj,
                    )
                    # Add data not used for matching
                    # obj.source_component = component_obj.id
                    print(component_obj)
                    obj.source_codesystem = component_obj.codesystem_id
                    obj.target_codesystem = component_obj.codesystem_id # Voor nu gelijk aan bron.
                    # TODO target nog aanpassen naar optie in formulier, om een doel-codesystem af te dwingen.
                    obj.status = status1
                    # obj.user = user # taken worden aangemaakt zonder gebruiker

                    # Save
                    obj.save()
                
                    db_hit = True

                    
                except Exception as e:
                    print("Component not found, or error: ", e)
                    db_hit = False
        
                handled.update({component : {
                    'form' : form,
                    'result' : db_hit,
                    'project' : project.title,
                    'component_id' : component_obj.id,
                    'component_title' : component_obj.component_title,
                }})
        else:
            print("###########################\n",form.errors,"\n", form.non_field_errors)
        return render(request, 'mapping/task_create.html', {
            'page_title': 'Mapping project',
            'project' : project,
            'projects' : project_list,
            'result': handled,
        })
    def get(self, request, **kwargs):
        projects = MappingProject.objects.all()
        project_list = []
        for project in projects:
            project_list.append((project.id, project.title))
        
        codesystems = MappingCodesystem.objects.all()
        codesystems_list = []
        for codesystem in codesystems:
            codesystems_list.append((codesystem.id, codesystem.codesystem_title+" - "+codesystem.codesystem_version))

        form = TaskCreateForm()

        return render(request, 'mapping/task_create.html', {
            'page_title': 'Mapping project',
            'form': form,
            'projects' : project_list,
            'codesystems' : codesystems_list,
        })

class UpdateSnomedPageView(UserPassesTestMixin,TemplateView):
    '''
    View used to update or fill a codesystem with Snomed concepts.
    Calls an async function from ./tasks.py, since this can take over 10 minutes.
    Only accessible with admin codesystem rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | admin codesystems').exists()
    
    def post(self, request, **kwargs):
        form = SnomedUpdateForm(request.POST)
        if form.is_valid():
            focus = str(form.cleaned_data['focus_concept'])
            codesystem = form.cleaned_data['codesystem']
            # Get task.id for tracking purposes
            task = import_snomed_async.delay(focus, codesystem)
            task_id = task.id
            print("TASK ID ******", task_id)
            return HttpResponseRedirect(reverse('mapping:index'))

    def get(self, request, **kwargs):
        # TODO - Check permissions for this
        form = SnomedUpdateForm()

        return render(request, 'mapping/update_snomed.html', {
            'page_title': 'Mapping project',
            'form': form,
        })

class UpdateNHGPageView(UserPassesTestMixin,TemplateView):
    '''
    View for updating of filling a codesystem with NHG data.
    Only accessible with admin codesystems rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | admin codesystems').exists()

    def post(self, request, **kwargs):
        # TODO - Check permissions for this
        form = NHGUpdateForm(request.POST)
        handled = {}
        if form.is_valid():
            df = read_excel('/webserver/mapping/resources/nhg/Ingrepentabel_v3.xls')
            for index, row in df.iterrows():
                codesystem = MappingCodesystem.objects.get(id=form.cleaned_data['codesystem'])
                obj, created = MappingCodesystemComponent.objects.get_or_create(
                    codesystem_id=codesystem,
                    component_id=row[0],
                )
                # Add data not used for matching
                obj.component_title     = row[1]
                obj.component_extra_1   = row[2]
                obj.component_extra_2   = row[3]
                obj.component_extra_3   = row[4]
                obj.component_extra_4   = row[5]
                obj.component_extra_5   = row[6]
                obj.component_extra_6   = row[7]
                obj.component_extra_7   = row[8]

                # Save
                obj.save()

                handled.update({row[0] : {
                    'result' : obj,
                    'codesystem_id' : form.cleaned_data['codesystem'],
                    'component_id' : row[0],
                    'component_title' : row[1],
                }})
        else:
            print("###########################\n",form.errors,"\n", form.non_field_errors)
        return render(request, 'mapping/update_nhg.html', {
            'page_title': 'Mapping project',
            'result': handled,
        })
    def get(self, request, **kwargs):
        # TODO - Check permissions for this
        form = NHGUpdateForm()

        return render(request, 'mapping/update_nhg.html', {
            'page_title': 'Mapping project',
            'form': form,
        })

class MappingIndexPageView(UserPassesTestMixin,TemplateView):
    '''
    View for choosing a project to work on.
    Only accessible with view tasks rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | view tasks').exists()

    def get(self, request, **kwargs):
        # TODO - Check if active projects exist, otherwise -> error.
        project_list = MappingProject.objects.filter(active=True)
        return render(request, 'mapping/index.html', {
            'page_title': 'Mapping project',
            'project_list': project_list,
        })

class ProjectIndexPageView(UserPassesTestMixin,TemplateView):
    '''
    Extremely convoluted view to allow a single-page overview of the current project.
    Also shows progress through time if the AjaxProgressRecordPageView is called at regular intervals.
    Only accessible with view tasks permissions.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | view tasks').exists()

    def get(self, request, **kwargs):
        # TODO - Check if project and task exist, otherwise -> redirect to project or homepage.

        # Taken per status
        try:
            current_user = User.objects.get(id=request.user.id)
            project_list = MappingProject.objects.filter(active=True)
            current_project = MappingProject.objects.get(id=kwargs.get('project'), active=True)
            tasks = MappingTask.objects.filter(user=current_user, project_id_id=current_project.id).exclude(status=current_project.status_complete).order_by('id')
            
            status_list = MappingTaskStatus.objects.filter(project_id=kwargs.get('project')).order_by('status_id')#.exclude(id=current_project.status_complete.id)
            tasks_per_status_labels = []
            tasks_per_status_values = []
            user_list = User.objects.filter()
            tasks_per_user_labels = []
            tasks_per_user_values = []
            for user in user_list:
                num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, user=user).exclude(status=current_project.status_complete).count()
                if num_tasks > 0:
                    num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, user=user).exclude(status=current_project.status_complete).count()
                    tasks_per_user_labels.append(user.username)
                    tasks_per_user_values.append(num_tasks)
            for status in status_list:            
                num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, status_id=status).count()
                tasks_per_status_labels.append(status.status_title)
                tasks_per_status_values.append(num_tasks)
        except:
            tasks_per_status_labels = []
            tasks_per_status_values = []
            tasks_per_user_labels = []
            tasks_per_user_values = []
            print("Error in 'taken per status'")
        
        # Taken per status huidige gebruiker
        try:
            tasks_current_user_status_labels = []
            tasks_current_user_status_values = []

            for status in status_list:
                tasks_current_user_status_labels.append(status.status_title)
            current_user = User.objects.get(id=request.user.id)
            num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, user=current_user).count()
            if num_tasks > 0:
                person_label = []
                person_value = []
                for status in status_list:
                    num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, status_id=status, user=current_user).count()
                    person_value.append(num_tasks)
                
                r = 255 * random.random()
                g = 255 * random.random()
                b = 255 * random.random()
                background_color = 'rgba({}, {}, {}, 0.2)'.format(r,g,b)
                border_color = 'rgba({}, {}, {}, 0.5)'.format(r,g,b)
                dataset = {
                    'label' : user.username,
                    'backgroundColor' : background_color,
                    'borderColor' : background_color,
                    'hoverBackgroundColor' : border_color,
                    'data': person_value
                }
                tasks_current_user_status_values.append(dataset)
                tasks_current_user_status_values = person_value
                
        except:
            tasks_current_user_status_labels = []
            tasks_current_user_status_values = []
            print("Error in 'taken per status'")


        # Taken per status per gebruiker
        try:
            tasks_user_status_labels = []
            tasks_user_status_values = []

            for status in status_list:
                tasks_user_status_labels.append(status.status_title)
            for user in user_list:
                num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, user=user).count()
                if num_tasks > 0:
                    person_label = []
                    person_value = []
                    for status in status_list:
                        num_tasks = MappingTask.objects.filter(project_id_id=current_project.id, status_id=status, user=user).count()
                        person_value.append(num_tasks)
                    
                    r = 255 * random.random()
                    g = 255 * random.random()
                    b = 255 * random.random()
                    background_color = 'rgba({}, {}, {}, 0.2)'.format(r,g,b)
                    border_color = 'rgba({}, {}, {}, 0.5)'.format(r,g,b)
                    dataset = {
                        'label' : user.username,
                        'backgroundColor' : background_color,
                        'borderColor' : background_color,
                        'hoverBackgroundColor' : border_color,
                        'data': person_value
                    }
                    tasks_user_status_values.append(dataset)
        except:
            tasks_user_status_labels = []
            tasks_user_status_values = []
            print("Error in 'taken per status'")

        # Statusverdeling door de tijd
        history = MappingProgressRecord.objects.filter(project=current_project, name="TasksPerStatus")
        time_labels = {}
        time_time = []
        for point in history:
            values = json.loads(point.values)
            for (index, value) in enumerate(values):
                # print(value['status'], value['num_tasks'])
                if value['status'] not in time_labels:
                    time_labels.update({value['status'] : []})
                time_labels[value['status']].append(value['num_tasks'])
            time_time.append(point.time.strftime("%Y-%m-%d %H:%M:%S"))
        time_dataset = []
        for index, value in time_labels.items():
            r = 255 * random.random()
            g = 255 * random.random()
            b = 255 * random.random()
            background_color = 'rgba({}, {}, {}, 0.2)'.format(r,g,b)
            border_color = 'rgba({}, {}, {}, 0.5)'.format(r,g,b)

            time_dataset.append({
                'label' : index,
                'data' : value,
                'fill' : 'false',
                'backgroundColor' : background_color,
                'borderColor' : background_color,
                'hoverBackgroundColor' : border_color,
                
            })

        print("current_user", current_user)
        print("project_list", project_list)
        print("current_project", current_project)
        print("TASKS", tasks)

        current_user = User.objects.get(id=request.user.id)
        project_list = MappingProject.objects.filter(active=True)
        current_project = MappingProject.objects.get(id=kwargs.get('project'), active=True)
        tasks = MappingTask.objects.filter(user=current_user, project_id_id=current_project.id).exclude(status=current_project.status_complete).order_by('id')
        total_num_tasks = len(tasks)
        if tasks.count() == 0:    
            tasks = MappingTask.objects.filter(project_id_id=current_project.id).exclude(status=current_project.status_complete).order_by('id')
            total_num_tasks = 0
                
        # print(task_list) # DEBUG
        
        # Lookup edit rights for mapping      
        db_permissions = request.user.groups.values_list('name', flat=True)
        permissions = []
        for perm in db_permissions:
            permissions.append(perm)
        print("Permissions: ", current_user.username, " -> ",permissions)


        # Render page
        return render(request, 'mapping/project_index.html', {
            'page_title': 'Mapping project',
            'current_project' :  current_project,
            'project_list': project_list,
            'first_task': tasks[0],
            'tasks_total' : total_num_tasks,
            'tasks_per_status_values' : tasks_per_status_values,
            'tasks_per_status_labels' : tasks_per_status_labels,
            'tasks_per_user_values' : tasks_per_user_values,
            'tasks_per_user_labels' : tasks_per_user_labels,
            'tasks_user_status_values' : tasks_user_status_values,
            'tasks_user_status_labels' : tasks_user_status_labels,
            'tasks_current_user_status_labels' : tasks_current_user_status_labels,
            'tasks_current_user_status_values' : tasks_current_user_status_values,
            'time_dataset' : time_dataset,
            'time_time' : time_time,
            'permissions' : permissions,
        })

        # return HttpResponseRedirect(reverse('homepage:index'))

class PostCommentPageView(UserPassesTestMixin,TemplateView):
    '''
    Handles posting a new comment.
    Only allowed with place comments rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | place comments').exists()

    def post(self, request, **kwargs):
        # TODO - Check permissions for this
        if request.method == 'POST':       
            form = PostCommentForm(request.POST)
            if form.is_valid():
                task = MappingTask.objects.get(id=form.cleaned_data.get('task_id'))
                user = User.objects.get(id=request.user.id)
                # print("User: ",user)
                obj = MappingComment.objects.create(
                    comment_body = form.cleaned_data.get('comment_body'),
                    comment_task = task,
                    comment_user = user,
                )
                
                # Save
                obj.save()
            return HttpResponseRedirect(reverse('mapping:index')+'project/'+str(form.cleaned_data.get('project_id'))+'/task/'+form.cleaned_data.get('task_id'))
        else:
            return HttpResponseRedirect(reverse('homepage:index'))

class DeleteCommentPageView(UserPassesTestMixin,TemplateView):
    '''
    Handles deleting a comment placed by the current user.
    Only allowed with place comments rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | place comments').exists()

    def get(self, request, **kwargs):
        try:
            current_user = User.objects.get(id=request.user.id)
            comment = MappingComment.objects.get(id=kwargs.get('comment_id'), comment_user=current_user)
            task = MappingTask.objects.get(id=comment.comment_task.id)
            comment.delete()
            return HttpResponseRedirect(reverse('mapping:index')+'project/'+str(task.project_id.id)+'/task/'+str(task.id))
        except Exception as e:
            return render(request, 'mapping/error.html', {
            'page_title': 'Error',
            'error_text': 'Mogelijk probeer je een commentaar aan te passen zonder dat deze door jou gemaakt is.',
            'exception' : e,
            })

# Update task status
class StatusUpdatePageView(UserPassesTestMixin,TemplateView):
    '''
    Handles changing the status of a task owned by the current user.
    Only allowed with change task status rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        return self.request.user.groups.filter(name='mapping | change task status').exists()

    def get(self, request, **kwargs):
        # Only do this on task owned by current user
        try:
            task = MappingTask.objects.get(id=kwargs.get('task'), user=request.user.id) #status
            current_user = User.objects.get(id=request.user.id)
            old_status = task.status.status_title
            old_task = str(task)
            status = MappingTaskStatus.objects.get(id=kwargs.get('status'))
            task.status = status
            task.save()

            user = User.objects.get(id=request.user.id)

            source_component = MappingCodesystemComponent.objects.get(id=task.source_component.id)
            mappingquery = MappingRule.objects.filter(source_component_id=source_component.id)
            mappingrules = {}
            for rule in mappingquery:
                mappingrules.update({rule.id : {
                    'Project ID' : rule.project_id.id,
                    'Project' : rule.project_id.title,
                    'Target component ID' : rule.target_component.component_id,
                    'Target component Term' : rule.target_component.component_title,
                    'Mapgroup' : rule.mapgroup,
                    'Mappriority' : rule.mappriority,
                    'Mapcorrelation' : rule.mapcorrelation,
                    'Mapadvice' : rule.mapadvice,
                    'Maprule' : rule.maprule,
                    'Active' : rule.active,
                }})

            event = MappingEventLog.objects.create(
                task=task,
                action='status_change',
                action_user=current_user,
                action_description='Status:',
                old_data='',
                new_data=str(mappingrules),
                old=old_status,
                new=task.status.status_title,
                user_source=user,
            )
            event.save()
            return HttpResponseRedirect(reverse('mapping:index')+'project/'+str(task.project_id.id)+'/task/'+kwargs.get('task'))
        except Exception as e:
            return render(request, 'mapping/error.html', {
            'page_title': 'Error',
            'error_text': 'Mogelijk probeer je een taak aan te passen die niet bestaat, of niet aan jou is toegewezen.',
            'exception' : e,
            })

class ChangeUserPageView(UserPassesTestMixin,TemplateView):
    '''
    Handles changing the user of any task.
    Only allowed with change task status rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | change task status').exists()


    def get(self, request, **kwargs):
        try:
            task = MappingTask.objects.get(id=kwargs.get('task')) #status
            old_task = str(task)
            current_user = User.objects.get(id=request.user.id)
            source_user = User.objects.get(id=task.user.id)
            target_user = User.objects.get(id=kwargs.get('user'))
            task.user = target_user
            task.save()

            source_component = MappingCodesystemComponent.objects.get(id=task.source_component.id)
            mappingquery = MappingRule.objects.filter(source_component_id=source_component.id)
            mappingrules = {}
            for rule in mappingquery:
                mappingrules.update({rule.id : {
                    'Project ID' : rule.project_id.id,
                    'Project' : rule.project_id.title,
                    'Target component ID' : rule.target_component.component_id,
                    'Target component Term' : rule.target_component.component_title,
                    'Mapgroup' : rule.mapgroup,
                    'Mappriority' : rule.mappriority,
                    'Mapcorrelation' : rule.mapcorrelation,
                    'Mapadvice' : rule.mapadvice,
                    'Maprule' : rule.maprule,
                    'Active' : rule.active,
                }})            
            # print(str(mappingrules))
            event = MappingEventLog.objects.create(
                    task=task,
                    action='user_change',
                    action_user=current_user,
                    action_description='Gebruiker:',
                    old_data='',
                    new_data=str(mappingrules),
                    old=str(source_user),
                    new=str(target_user),
                    user_source=source_user,
                    user_target=target_user,
                )
            event.save()
            return HttpResponseRedirect(reverse('mapping:index')+'project/'+str(task.project_id.id)+'/task/'+kwargs.get('task'))
        except Exception as e:
            return render(request, 'mapping/error.html', {
            'page_title': 'Error',
            'error_text': 'Mogelijk probeer je een taak aan te passen die niet bestaat, of niet aan jou is toegewezen.',
            'exception' : e,
            })

# Filter task list on status
class StatusFilterPageView(UserPassesTestMixin,TemplateView):
    '''
    Handles changing the statusfilter in the taskmanager task list.
    Only allowed with view task rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | view tasks').exists()


    def get(self, request, **kwargs):
        # TODO - Add event to event log
        if kwargs.get('status'):
            request.session['status_filter'] = kwargs.get('status')
        if kwargs.get('own_tasks'):
            request.session['own_task_filter'] = kwargs.get('own_tasks')
        return HttpResponseRedirect(reverse('mapping:index')+'project/'+kwargs.get('project')+'/task/'+kwargs.get('task'))
        
        # TODO - error handling - als geen taak gevonden -> naar index als straf

class AuditPageView(UserPassesTestMixin,TemplateView):
    '''
    Handles generating audit reports for mapping rules.
    Only allowed with audit rights.
    TODO - should be moved to a collection of async tasks with saving results as soon as projects get larger.
    '''

    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | audit').exists()

    def get(self, request, **kwargs):
        audit_types = (
            'run_async',
            'multiple_mappings',
        )
        project = kwargs.get('project')
        current_audit = kwargs.get('audit_type')

        if current_audit == "run_async":
            task = audit_async.delay('multiple_mapping', project)
            task_id = task.id
            print("TASK ID ******", task_id)

            return render(request, 'mapping/notice.html', {
            'page_title': 'Succes',
            'header' : 'Audit tool',
            'notice_text': 'Alle audits worden op de achtergrond uitgevoerd. Resultaten zijn te zien via /show.',
            'extra' : '',
            })
        elif current_audit == "show":
            tasks = MappingTask.objects.filter(project_id=project).order_by('id')
            data = []
            for task in tasks:
                audits = MappingTaskAudit.objects.filter(task=task)
                if audits.count() > 0:
                    for audit in audits:
                        data.append(audit)

            audits_total = len(tasks)
            audits_max_page = 50

            # Paginate task list #
            # Number of tasks per page
            paginator = Paginator(data, audits_max_page)
            # Get correct page
            try:
                page = request.GET.get('page')
                objects = paginator.page(page)
            except PageNotAnInteger:
                objects = paginator.page(1)
            except EmptyPage:
                objects = paginator.page(paginator.num_pages)
            
            return render(request, 'mapping/audit_results.html', {
            'page_title': 'Alle audit resultaten',
            'heading': 'Alle audit resultaten voor het huidige project',
            'project_id' : project,
            'objects' : objects,
            })
        

        # LEGACY Audit - report all multiple mappings
        if current_audit == "multiple_mappings":
            task_map_list = []
            # Get all tasks in project
            tasks = MappingTask.objects.filter(project_id_id=project)
            # print("TASKS ",tasks.count())
            for task in tasks:
                mappings = MappingRule.objects.filter(
                    source_component = task.source_component,
                    project_id_id = project
                ).order_by('mappriority')
                mapping_info = []
                for mapping in mappings:
                    mapcorrelation = mapping.mapcorrelation
                    if mapcorrelation == "447559001":
                        mapcorrelation = "Broad to narrow"
                    if mapcorrelation == "447557004":
                        mapcorrelation = "Exact match"
                    if mapcorrelation == "447558009":
                        mapcorrelation = "Narrow to broad"
                    if mapcorrelation == "447560006":
                        mapcorrelation = "Partial overlap"
                    if mapcorrelation == "447556008":
                        mapcorrelation = "Not mappable"
                    if mapcorrelation == "447561005":
                        mapcorrelation = "Not specified"

                    mapping_info.append({
                        'target_component' : mapping.target_component,
                        'mapcorrelation' : mapcorrelation,
                        'mapadvice' : mapping.mapadvice,
                        'mappriority' : mapping.mappriority,
                    })
                if mappings.count() > 1:
                    task_map_list.append({
                        'task_id' : task.id,
                        'source_component' : task.source_component,
                        'num_mappings' : mappings.count(),
                        'mapping_info' : mapping_info,
                    })
            # print(task_map_list)
            # Render page
            return render(request, 'mapping/task_audit.html', {
                'page_title': 'Mapping project',
                'task_list' : task_map_list,
                'project_id' : project,
                'number_audit_hits' : len(task_map_list),
            })

class TaskManagerPageView(UserPassesTestMixin,TemplateView):
    '''
    The taskmanager pageview. Handles most everything in assigning tasks.
    Only allowed with create tasks rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | create tasks').exists()

    def post(self, request, **kwargs):
        if request.method == 'POST':
            TaskManagerFormSet = formset_factory(TaskManagerForm, can_delete=True)
            formset = TaskManagerFormSet(request.POST)
            for form in formset:
                # form.fields['target_component'].required = False
                # form.fields['source_component'].required = False
                # form.fields['user'].required = False
                if formset.is_valid():
                    print("Form valid")
                    print(form.cleaned_data.get('task_id'), form.cleaned_data.get('checkbox'), request.POST.get('username'))
                    # Find task
                    task = MappingTask.objects.get(id=form.cleaned_data.get('task_id'))
                    # If requested, change username
                    if request.POST.get('username') != "0" and form.cleaned_data.get('checkbox'):
                        new_user = User.objects.get(id=request.POST.get('username'))
                        task.user = new_user
                    if request.POST.get('statuschange') != "0" and form.cleaned_data.get('checkbox'):
                        new_status = MappingTaskStatus.objects.get(id=request.POST.get('statuschange'))
                        task.status = new_status
                    task.save()

                else:
                    print("Form not valid")
                    print("###########################\n",form.errors,"\n", form.non_field_errors)
        return HttpResponseRedirect(reverse('mapping:index')+'taskmanager/'+str(kwargs.get('project')))
        # return HttpResponseRedirect(reverse('homepage:index'))


    def get(self, request, **kwargs):
        # TODO - Check if project exist, otherwise -> redirect to project or homepage.

        project_list = MappingProject.objects.all()
        all_users = User.objects.all()
        current_project = MappingProject.objects.get(id=kwargs.get('project'))
        all_statuses = MappingTaskStatus.objects.filter(project_id=current_project)

        # Set statusfilter if needed, otherwise make it 0
        if request.GET.get('status_filter'):
            request.session['status_filter'] = int(request.GET.get('status_filter'))
        elif request.session.get('status_filter') == None:
            request.session['status_filter'] = 0
        print("STATUS FILTER1 ", request.session.get('status_filter'))

        # Create task list
        if request.session.get('status_filter') == 0 or request.session.get('status_filter') == None or request.session.get('status_filter') == 0:
            tasks = MappingTask.objects.filter(project_id=kwargs.get('project')).order_by('id')#.exclude(status=current_project.status_complete)
            request.session['status_filter'] = 0
        else:
            tasks = MappingTask.objects.filter(project_id=kwargs.get('project'), status=request.session['status_filter']).order_by('id')#.exclude(status=current_project.status_complete)

        print("USER FILTER1 ", request.session.get('user_filter'))
        # Set user filter session if requested
        if request.GET.get('user_filter'):
            request.session['user_filter'] = int(request.GET.get('user_filter'))
        # Set user filter session to 0 if none present
        elif request.session.get('user_filter') == None or not request.session.get('user_filter'):
            request.session['user_filter'] = 0
        print("USER FILTER1 ", request.session.get('user_filter'))

        # Set user filter on query if needed
        if request.session['user_filter'] == -1:
            tasks = tasks
        elif request.session['user_filter'] == 0:
            print("GEEN GBRUIKER QUERY")
            tasks = tasks.filter(user_id=None)
        else:
            print("SPECIFIEKE GEBRUIKER QUERY")
            tasks = tasks.filter(user_id=request.session['user_filter'])


        # Number of tasks per page
        try:
            if request.GET.get('numpage') and int(request.GET.get('numpage')) <= 1000:
                paginator = Paginator(tasks, int(request.GET.get('numpage')))
            else:
                paginator = Paginator(tasks, 50)
        except:
            paginator = Paginator(tasks, 50)

        # Get correct page
        try:
            page = request.GET.get('page')
            objects = paginator.page(page)
        except PageNotAnInteger:
            objects = paginator.page(1)
        except EmptyPage:
            objects = paginator.page(paginator.num_pages)

        # Create dictionary to use as initial data in formset
        task_list = []
        for task in objects:
            try:
                username = task.user.username
            except:
                username = "Geen gebruiker"
            task_list.append({
                'task_id' : task.id,
                'source_component' : task.source_component.component_title,
                'status' : task.status.status_title,
                'user' : username,
            })
        
        # Create formset
        TaskManagerFormSet = formset_factory(TaskManagerForm, extra=0)
        formset = TaskManagerFormSet(initial=task_list)
        
        # Render page
        return render(request, 'mapping/taskmanager.html', {
            'page_title': 'Mapping project',
            'project_list' :  project_list,
            'all_statuses' : all_statuses,
            'all_users' : all_users,
            'current_project' : current_project,
            'status_filter' : request.session['status_filter'],
            'user_filter' : request.session['user_filter'],
            'objects' : objects,
            'formset' : formset,
        })

# Task editor
class TaskEditorPageView(UserPassesTestMixin,TemplateView):
    '''
    The main taskeditor. Handles most everything to do with creating and editing mappings.
    Only allowed with view task rights.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        return self.request.user.groups.filter(name='mapping | view tasks').exists()

    def post(self, request, **kwargs):
        # TODO - Check if project and task exist, otherwise -> error or redirect to project or homepage.
        # Save mappings if submitted
        if request.method == 'POST':
            MappingFormSet = formset_factory(MappingForm, can_delete=True)
            formset = MappingFormSet(request.POST)
            for form in formset:
                form.fields['id'].required = False
                form.fields['target_component_ident'].required = False
                form.fields['target_component_codesystem'].required = False
                form.fields['target_component_term'].required = False
                dropdown_target = form.prefix+'-'+'target_component'
                target_component_id = request.POST.get(dropdown_target)
                delete_yesno = form.prefix+'-'+'DELETE'
                delete_yesno = request.POST.get(delete_yesno)
                print("###########################\n",form.errors,"\n", form.non_field_errors)
                if form.is_valid() and target_component_id != 'None':
                    print("ID: ",form.cleaned_data.get('id'))
                    print("Source: ",form.cleaned_data.get('source_component'))
                    print("Target: ",target_component_id)
                    print("Active: ",form.cleaned_data.get('active'))
                    print("Delete: ",delete_yesno)
                    print("valid? ",form.is_valid()) # DEBUG

                    # print("Valid, saved - #",form.cleaned_data.get('id')) # DEBUG
                    try:
                        # If object with this ID exists -> update
                        if form.cleaned_data.get('id') == None:
                            print("NONE - set to 0")
                                                
                        target_component = MappingCodesystemComponent.objects.get(id=target_component_id)
                        source_component = MappingCodesystemComponent.objects.get(id=form.cleaned_data.get('source_component'))
                        project = MappingProject.objects.get(id=int(kwargs.get('project')))
                        print("Target component: ",target_component)
                        if delete_yesno == 'on':
                            obj = MappingRule.objects.get(id=form.cleaned_data.get('id')).delete()
                            print(obj, "deleted")
                        else:
                            obj = MappingRule.objects.get(id=form.cleaned_data.get('id'))
                            obj.project_id.id=project
                            obj.target_component=target_component

                            obj.mapgroup=form.cleaned_data.get('mapgroup')
                            obj.mappriority=form.cleaned_data.get('mappriority')
                            obj.mapcorrelation=form.cleaned_data.get('mapcorrelation')
                            obj.mapadvice=form.cleaned_data.get('mapadvice')
                            obj.maprule=form.cleaned_data.get('maprule')

                            obj.active = form.cleaned_data.get('active')
                            obj.save()

                        print("Object exists") # DEBUG
                    except Exception as e:
                        print (e)
                        # If object with this ID does not exist -> create
                        print("Object does not exist") # DEBUG
                        target_component = MappingCodesystemComponent.objects.get(id=target_component_id)
                        source_component = MappingCodesystemComponent.objects.get(id=form.cleaned_data.get('source_component'))
                        project = MappingProject.objects.get(id=int(kwargs.get('project')))
                        obj = MappingRule.objects.create(
                            project_id=project,
                            source_component=source_component,
                            target_component=target_component,
                            mapgroup=form.cleaned_data.get('mapgroup'),
                            mappriority=form.cleaned_data.get('mappriority'),
                            mapcorrelation=form.cleaned_data.get('mapcorrelation'),
                            mapadvice=form.cleaned_data.get('mapadvice'),
                            maprule=form.cleaned_data.get('maprule'),
                            active = form.cleaned_data.get('active')
                            )
                        obj.save()
                        print("Object created")
                    # Save object
                else:
                    print("Not valid or empty target, not saved") # DEBUG
            # Start audit on current item
            audit_async.delay('multiple_mapping', kwargs.get('project'), kwargs.get('task'))
                
            return HttpResponseRedirect(reverse('mapping:index')+'project/'+str(kwargs.get('project'))+'/task/'+str(kwargs.get('task')))
        else:
            return HttpResponseRedirect(reverse('homepage:index'))
    
    def get(self, request, **kwargs):
        # TODO - Check if project and task exist, otherwise -> redirect to project or homepage.

        project_list = MappingProject.objects.values_list('id').filter(active=True)
        current_user = User.objects.get(id=request.user.id)
        current_project = MappingProject.objects.get(id=kwargs.get('project'), active=True)

        # Standard - filter on only own tasks
        if request.session.get('own_task_filter') == None:
            request.session['own_task_filter'] = 1

        # Status manager
        status_list = MappingTaskStatus.objects.filter(project_id=kwargs.get('project')).order_by('status_id')#.exclude(id=current_project.status_complete.id) # Do not filter the published status! Otherwise you can't assign it
        
        # User list
        user_list = User.objects.all().order_by('username')

        # Create comments form
        comments_form = PostCommentForm(initial={
            'project_id': kwargs.get('project'),
            'task_id': kwargs.get('task'),
            })

        # Create dictionary for events (ie. should look for all actions and comments, combine them into a dict)
        events_list = []
        comments = MappingComment.objects.filter(comment_task=kwargs.get('task')).order_by('-comment_created') 
        for item in comments:
            events_list.append({
                'id' : item.id,
                'text' : item.comment_body,
                'type' : 'comment',
                'user' : item.comment_user.username, # achtervoegsel voor overige velden zoals user.email
                'created' : item.comment_created,
            })
        events = MappingEventLog.objects.filter(task_id=kwargs.get('task')).order_by('-event_time') 
        for item in events:
            data =  json.dumps(item.new_data, sort_keys=True, indent=4)
            try:
                action_user = item.action_user.username
            except:
                action_user = item.user_source.username
            events_list.append({
                'text' : action_user + ': ' + item.old + ' -> ' + item.new,
                'data' : data,
                'action_user' : item.action_user,
                'type' : item.action,
                'user' : item.user_source.username, # achtervoegsel voor overige velden zoals user.email
                'created' : item.event_time,
            })
        # Sort event_list on date
        events_list.sort(key=lambda item:item['created'], reverse=True)

        # Lookup edit rights for mapping      
        db_permissions = request.user.groups.values_list('name', flat=True)
        permissions = []
        for perm in db_permissions:
            permissions.append(perm)
        print("Page loaded by: ", current_user.username)
        print("Permissions: ", permissions)

        # Create task list with filters
        if request.session.get('status_filter') == "0" or request.session.get('status_filter') == None or request.session.get('status_filter') == 0:
            request.session['status_filter'] = 0
            if request.session.get('own_task_filter') == "0" or request.session.get('own_task_filter') == None or request.session.get('own_task_filter') == 0:
                tasks = MappingTask.objects.filter(project_id=kwargs.get('project')).order_by('id').exclude(status=current_project.status_complete)
                request.session['own_task_filter'] = 0
            else:
                tasks = MappingTask.objects.filter(project_id=kwargs.get('project'), user=current_user).order_by('id').exclude(status=current_project.status_complete)
        else:
            if request.session.get('own_task_filter') == "0" or request.session.get('own_task_filter') == None or request.session.get('own_task_filter') == 0:
                tasks = MappingTask.objects.filter(project_id=kwargs.get('project'), status=request.session['status_filter']).order_by('id').exclude(status=current_project.status_complete)
                request.session['own_task_filter'] = 0
            else:
                tasks = MappingTask.objects.filter(project_id=kwargs.get('project'), status=request.session['status_filter'], user=current_user).order_by('id').exclude(status=current_project.status_complete)

        tasks_total = len(tasks)
        tasks_max_page = 20

        # Paginate task list #
        # Number of tasks per page
        paginator = Paginator(tasks, tasks_max_page)
        # Get correct page
        try:
            page = request.GET.get('page')
            objects = paginator.page(page)
        except PageNotAnInteger:
            objects = paginator.page(1)
        except EmptyPage:
            objects = paginator.page(paginator.num_pages)

        task_list = {}
        for task in objects[:tasks_max_page]:
            # print("TASK: ",task.id) # DEBUG
            # Fetch data from other tables
            # print(task.project_id.id)
            project = MappingProject.objects.get(id=task.project_id.id)
            source_codesystem = MappingCodesystem.objects.get(id=task.source_codesystem.id)
            target_codesystem = MappingCodesystem.objects.get(id=task.target_codesystem.id)
            component = MappingCodesystemComponent.objects.get(id=task.source_component.id)
            
            # Fill dictionary with data from current task
            task_list.update({
                task.id : {
                    'id' : task.id,
                    'project_id' : task.project_id.id,
                    'project_title' : project.title,
                    'source_component_id' : task.source_component.id,
                    'source_component_title' : component.component_title,
                    'source_codesystem' : source_codesystem.codesystem_title,
                    'target_codesystem' : target_codesystem.codesystem_title,
                    'user' : task.user,
                    'status' : task.status,
                    'task_created' : task.task_created,
                    }
            })

        # Source concept
        current_task = MappingTask.objects.get(id=kwargs.get('task')) 
        current_codesystem = MappingCodesystem.objects.get(id=current_task.source_codesystem.id) 
        componentQuery = MappingCodesystemComponent.objects.get(id=current_task.source_component.id)
        source_component = {
            'codesystem' : current_codesystem.codesystem_title,
            'codesystem_version' : current_codesystem.codesystem_version,
            'component_id' : componentQuery.component_id,
            'title' : componentQuery.component_title,
            'extra_1' : componentQuery.component_extra_1,
            'extra_2' : componentQuery.component_extra_2,
            'extra_3' : componentQuery.component_extra_3,
            'extra_4' : componentQuery.component_extra_4,
            'extra_5' : componentQuery.component_extra_5,
            'extra_6' : componentQuery.component_extra_6,
            'extra_7' : componentQuery.component_extra_7,
            'status' : current_task.status.id,
        }

        context = {
            'page_title': 'Mapping project',
            'current_project' :  current_project,
            'current_codesystem' :  current_codesystem,
            'current_task' :  current_task,
            'project_list': project_list,
            'tasks': task_list,
            'tasks_total' : tasks_total,
            'tasks_shown' : len(task_list),
            'objects'   : objects,
            'comments_form' : comments_form,
            'source_component' : source_component,
            'current_user' : current_user,
            'events' : events_list,
            'status_list' : status_list,
            'user_list' : user_list,
            'own_task_filter' : int(request.session.get('own_task_filter')),
            'status_filter' : int(request.session.get('status_filter')),
            'permissions' : permissions,
        }

        # Render page
        if current_project.project_type == "1":
            return render(request, 'mapping/1-n/task_editor.html', context)
        elif current_project.project_type == "2":
            return render(request, 'mapping/n-1/task_editor.html', context)

class MappingTargetListPageView(UserPassesTestMixin,TemplateView):
    '''
    Renders mapping targets, for use with Ajax request.
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        return self.request.user.groups.filter(name='mapping | view tasks').exists()

    def get(self, request, **kwargs):

        current_task = MappingTask.objects.get(id=kwargs.get('task')) 
        componentQuery = MappingCodesystemComponent.objects.get(id=current_task.source_component.id)
        current_project = MappingProject.objects.get(id=current_task.project_id.id, active=True)

        # Fetch mappings
        mappings = MappingRule.objects.filter(
            source_component=current_task.source_component,
            project_id=current_task.project_id,
            ).order_by('-active', 'mappriority')
        mapping_list = []
        for mapping in mappings:
            component_data = MappingCodesystemComponent.objects.get(id=mapping.target_component.id)
            codesystem_data = MappingCodesystem.objects.get(id=component_data.codesystem_id.id)
            mapping_list.append({
                    'id' : mapping.id,
                    # 'project_id' : mapping.project_id,
                    'source_component' : mapping.source_component.id,
                    'target_component' : mapping.target_component.id,
                    'target_component_codesystem' : codesystem_data.codesystem_title,
                    'target_component_term' : component_data.component_title,
                    'target_component_ident' : component_data.component_id,
                    'mapgroup' : mapping.mapgroup,
                    'mappriority' : mapping.mappriority,
                    'mapcorrelation' : mapping.mapcorrelation,
                    'mapadvice' : mapping.mapadvice,
                    'maprule' : mapping.maprule,
                    'active' : mapping.active,
                })
        
        # Put mappings in forms
        MappingFormSet = formset_factory(MappingForm, can_delete=True)
        formset = MappingFormSet(initial=mapping_list)
        
        # Set default content for the extra form to allow entering a new mapping
        try:
            mappriority_next = mapping_list[-1].get('mappriority')+1
        except:
            mappriority_next = 1
        formset[len(formset)-1]['source_component'].initial = current_task.source_component.id
        formset[len(formset)-1]['active'].initial = True
        formset[len(formset)-1]['mappriority'].initial = mappriority_next
        formset[len(formset)-1]['mapadvice'].initial = "Altijd"
        
        # Lookup edit rights for mapping      
        current_user = User.objects.get(id=request.user.id)
        db_permissions = request.user.groups.values_list('name', flat=True)
        permissions = []
        for perm in db_permissions:
            permissions.append(perm)
        
        return render(request, 'mapping/1-n/mapping_target_list_v2.html', {
            'page_title': 'Commentaar',
            'formset' : formset,
            'current_task' : current_task,
            'current_user' : current_user,
            'permissions': permissions,
            'current_project' : current_project,
        })


class ViewEventsPageView(UserPassesTestMixin,TemplateView):
    '''
    View for rendering all events, for use in Ajax call
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | place comments').exists()

    def get(self, request, **kwargs):
        # Create dictionary for events (ie. should look for all actions and comments, combine them into a dict)
        events_list = []
        current_user = User.objects.get(id=request.user.id)
        comments = MappingComment.objects.filter(comment_task=kwargs.get('task')).order_by('-comment_created') 
        for item in comments:
            events_list.append({
                'id' : item.id,
                'text' : item.comment_body,
                'type' : 'comment',
                'user' : item.comment_user.username, # achtervoegsel voor overige velden zoals user.email
                'created' : item.comment_created,
            })
        events = MappingEventLog.objects.filter(task_id=kwargs.get('task')).order_by('-event_time') 
        for item in events:
            data =  json.dumps(item.new_data, sort_keys=True, indent=4)
            try:
                action_user = item.action_user.username
            except:
                action_user = item.user_source.username
            events_list.append({
                'text' : action_user + ': ' + item.old + ' -> ' + item.new,
                'data' : data,
                'action_user' : item.action_user,
                'type' : item.action,
                'user' : item.user_source.username, # achtervoegsel voor overige velden zoals user.email
                'created' : item.event_time,
            })
        # Sort event_list on date
        events_list.sort(key=lambda item:item['created'], reverse=True)

        return render(request, 'mapping/events.html', {
            'page_title': 'Commentaar',
            'current_user' : current_user,
            'events': events_list,
        })

class GetCurrentStatus(UserPassesTestMixin,TemplateView):
    '''
    View for getting AJAX requests for current status of task
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | view tasks').exists()

    def get(self, request, **kwargs):
        current_task = MappingTask.objects.get(id=kwargs.get('task')) 
        current_user = User.objects.get(id=request.user.id)
        
        # Status manager
        status_list = MappingTaskStatus.objects.filter(project_id=current_task.project_id.id).order_by('status_id')
        # Lookup permissions      
        db_permissions = request.user.groups.values_list('name', flat=True)
        permissions = []
        for perm in db_permissions:
            permissions.append(perm)
        
        return render(request, 'mapping/current_task_status.html', {
        'current_user' : current_user,
        'current_task' : current_task,
        'status_list' : status_list,
        'permissions' : permissions,
        })

class GetAuditsForTask(UserPassesTestMixin,TemplateView):
    '''
    View for requesting audit hits for current task
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | view tasks').exists()

    def get(self, request, **kwargs):
        task = MappingTask.objects.get(id=kwargs.get('task'))
        audits = MappingTaskAudit.objects.filter(task=task)
        
        return render(request, 'mapping/audit_results_current_task.html', {
        'page_title': 'Audit results',
        'audits' : audits,
        })

class AjaxTestView(UserPassesTestMixin,TemplateView):
    '''
    View for testing AJAX requests
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord')
        return self.request.user.groups.filter(name='mapping | place comments').exists()

    def get(self, request, **kwargs):
        
        return render(request, 'mapping/ajax_test.html', {
        'page_title': 'Error',
        'error_text': 'Mogelijk probeer je een commentaar aan te passen zonder dat deze door jou gemaakt is.',
        })