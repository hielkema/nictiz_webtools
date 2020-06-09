# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .models import *
from mapping.models import *
import time, json
from urllib.request import urlopen, Request
import urllib.parse
import environ
from snowstorm_client import Snowstorm

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))


@shared_task
def generate_snomed_tree(payload):

    snowstorm = Snowstorm(
            baseUrl="https://snowstorm.test-nictiz.nl",
            # baseUrl="https://snowstorm.ihtsdotools.org/snowstorm/snomed-ct",
            debug=True,
            preferredLanguage="nl",
            defaultBranchPath="MAIN/SNOMEDCT-NL",
        )

    conceptid = payload.get('conceptid')
    refset = payload.get('refset')
    db_id = payload.get('db_id')

    def list_children(focus):
        component = MappingCodesystemComponent.objects.get(component_id=focus)
        
        _children = []
        if component.children != None:
            for child in list(json.loads(component.children)):
                _children.append(list_children(child))
        test = snowstorm.findConcepts(ecl=f"{component.component_id} AND ^{str(refset)}")
        print(test)
        
        refsets = snowstorm.getMapMembers(id=str(refset), referencedComponentId=str(component.component_id))
        if len(refsets) > 0:
            refsets = True
        else:
            refsets = False

        output = {
            'id' : focus,
            'name' : component.component_title,

            'component_id' : component.component_id,
            'component_title' : component.component_title,
            'refsets' : refsets,

            'children' : _children
        }
        
        return(output)

    print('Get tree for',str(conceptid))
    children_list = [list_children(conceptid)]

    obj = SnomedTree.objects.get(id = db_id)
    
    obj.data = children_list
    obj.finished = True

    obj.save()

    return True


@shared_task
def fetch_termspace_tasks():
    # Define load tasks function - returns content as dict
    def load_tasks(token='geen', published='true', limit=5000, skip=0):
        try:
            url = "https://nl-prod-main.termspace.com/api/workflow/nl-edition/workflow/instances/112?projectId=57be297bc9fbcde30c573aa0&access_token={token}&excludePublished=false&viewPublished={published}&workList=asd&dontUseWorklist=true&limit={limit}&skip={skip}".format(
                token=token.token, 
                published=published,
                limit=limit,
                skip=skip,
            )

            req = Request(url)
            response = urlopen(req).read()
            response = json.loads(response)
            return response
        except Exception as e:
            print('Error in retrieving tasks', e)
            return None

    try:
        token = TermspaceMeta.objects.get(username=env('termspace_user3'))

        tasks = []
        start = 0
        limit = 1000
        while True:
            result = load_tasks(token=token, skip=start, limit=limit, published='false')
            for item in result:
                tasks.append(item)
                
            start += limit
            print('Interval: got {tasks}.'.format(tasks=len(tasks)))
            if len(result) == 0: break
        start = 0
        limit = 1000
        while True:
            result = load_tasks(token=token, skip=start, limit=limit, published='true')
            for item in result:
                tasks.append(item)
                
            start += limit
            print('Interval: got {tasks}.'.format(tasks=len(tasks)))
            if len(result) == 0: break

        # Handle tasks, enter into db
        for task in tasks:
            obj, created = TermspaceTask.objects.get_or_create(task_id = str(task.get('_id')))
            obj.data = task
            obj.save()

        output = len(tasks)


        
    except Exception as e:
        print(e)
        # Refresh token
        url = 'https://nl-prod-main.termspace.com/api/users/login'
        data = urllib.parse.urlencode({
            'username' : env('termspace_user3'),
            'password' : env('termspace_pass3'),
        })
        data = data.encode('ascii')
        req = urllib.request.Request(url, data)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())

        token = result.get('token') 

        obj,created = TermspaceMeta.objects.get_or_create(username=env('termspace_user3'))
        obj.token = token
        obj.save()

        output = str(e)
        fetch_termspace_tasks.delay()


    return(output)

@shared_task
def dump_termspace_progress():
    output = []


    ######### Overal status distribution over all tasks #########
    # Semantic review / problem, 2019, volkert
    sem = TermspaceTask.objects.filter(
        data__folder__icontains = '2019',
        data__assignee = 'volkert',
        data__workflowState = 'semantic review',
    )
    prob = TermspaceTask.objects.filter(
        data__folder__icontains = '2019',
        data__assignee = 'volkert',
        data__workflowState = 'problem',
    )
    obj = TermspaceProgressReport.objects.create(
        tag = 'SemanticProblem2019volkert',
        title = 'Semantic review / Problem, _2019, volkert',
        description = 'Alle taken op Volkert, in een map met naam (.*)2019(.*), en status semantic review of problem.',
        count = sem.count() + prob.count(),
    )
    output.append(str(obj))

    # Semantic review / problem, volkert
    sem = TermspaceTask.objects.filter(
        data__assignee = 'volkert',
        data__workflowState = 'semantic review',
    )
    prob = TermspaceTask.objects.filter(
        data__assignee = 'volkert',
        data__workflowState = 'problem',
    )
    obj = TermspaceProgressReport.objects.create(
        tag = 'SemanticProblemVolkert',
        title = 'Semantic review / Problem, volkert',
        description = 'Alle taken op Volkert en status semantic review of problem.',
        count = sem.count() + prob.count(),
    )
    output.append(str(obj))

    # Medical review, 2019, volkert
    query = TermspaceTask.objects.filter(
        data__folder__icontains = '2019',
        data__assignee = 'volkert',
        data__workflowState = 'medical review',
    )
    obj = TermspaceProgressReport.objects.create(
        tag = 'Medical2019volkert',
        title = 'Medical review, _2019, volkert',
        description = 'Alle taken op Volkert, in een map met naam (.*)2019(.*), en status medical review.',
        count = query.count(),
    )
    output.append(str(obj))

    # Medical review, volkert
    query = TermspaceTask.objects.filter(
        data__assignee = 'volkert',
        data__workflowState = 'medical review',
    )
    obj = TermspaceProgressReport.objects.create(
        tag = 'Medical2019volkert',
        title = 'Medical review, volkert',
        description = 'Alle taken op Volkert en status medical review.',
        count = query.count(),
    )
    output.append(str(obj))

    # incomplete CAT, 2019, volkert
    query = TermspaceTask.objects.filter(
        data__folder__icontains = '2019',
        data__assignee = 'volkert',
        data__workflowState = 'incomplete CAT',
    )
    obj = TermspaceProgressReport.objects.create(
        tag = 'incompleteCAT2019volkert',
        title = 'incomplete CAT, _2019, volkert',
        description = 'Alle taken in een map met naam (.*)2019(.*), en status incomplete CAT.',
        count = query.count(),
    )
    output.append(str(obj))

    # Medical review
    query = TermspaceTask.objects.filter(
        data__workflowState = 'medical review',
    )
    obj = TermspaceProgressReport.objects.create(
        tag = 'Medical',
        title = 'Alle medical review',
        description = 'Alle taken met status medical review.',
        count = query.count(),
    )
    output.append(str(obj))

    # Semantic review
    query = TermspaceTask.objects.filter(
        data__workflowState = 'semantic review',
    )
    obj = TermspaceProgressReport.objects.create(
        tag = 'Medical',
        title = 'Alle semantic review',
        description = 'Alle taken met status semantic review.',
        count = query.count(),
    )
    output.append(str(obj))

    # Problem
    query = TermspaceTask.objects.filter(
        data__workflowState = 'problem',
    )
    obj = TermspaceProgressReport.objects.create(
        tag = 'Medical',
        title = 'Alle problem',
        description = 'Alle taken met status problem.',
        count = query.count(),
    )
    output.append(str(obj))

    # IHTSDO
    query = TermspaceTask.objects.filter(
        data__workflowState = 'IHTSDO',
    )
    obj = TermspaceProgressReport.objects.create(
        tag = 'IHTSDO',
        title = 'Alle IHTSDO',
        description = 'Alle taken met status IHTSDO.',
        count = query.count(),
    )
    output.append(str(obj))

    # IHTSDO submitted
    query = TermspaceTask.objects.filter(
        data__workflowState = 'IHTSDO - submitted',
    )
    obj = TermspaceProgressReport.objects.create(
        tag = 'IHTSDOsubmitted',
        title = 'Alle IHTSDO submitted',
        description = 'Alle taken met status IHTSDO submitted.',
        count = query.count(),
    )
    output.append(str(obj))

    # Specialist consulted
    query = TermspaceTask.objects.filter(
        data__workflowState = 'specialist consulted',
    )
    obj = TermspaceProgressReport.objects.create(
        tag = 'specialistConsulted',
        title = 'Alle specialist consulted',
        description = 'Alle taken met status specialist consulted.',
        count = query.count(),
    )
    output.append(str(obj))

    # Waiting for specialist
    query = TermspaceTask.objects.filter(
        data__workflowState = 'waiting for specialist',
    )
    obj = TermspaceProgressReport.objects.create(
        tag = 'waitingSpecialist',
        title = 'Alle waiting for specialist',
        description = 'Alle taken met status waiting for specialist.',
        count = query.count(),
    )
    output.append(str(obj))

    # Translation
    query = TermspaceTask.objects.filter(
        data__workflowState = 'translation',
    )
    obj = TermspaceProgressReport.objects.create(
        tag = 'ranslation',
        title = 'Alle translation',
        description = 'Alle taken met status translation.',
        count = query.count(),
    )
    output.append(str(obj))

    # Revision
    query = TermspaceTask.objects.filter(
        data__workflowState = 'revision',
    )
    obj = TermspaceProgressReport.objects.create(
        tag = 'revision',
        title = 'Alle revision',
        description = 'Alle taken met status revision.',
        count = query.count(),
    )
    output.append(str(obj))
    
    # Quality control
    query = TermspaceTask.objects.filter(
        data__workflowState = 'quality control',
    )
    obj = TermspaceProgressReport.objects.create(
        tag = 'qualityControl',
        title = 'Alle quality control',
        description = 'Alle taken met status quality control.',
        count = query.count(),
    )
    output.append(str(obj))
    
    # Discussion
    query = TermspaceTask.objects.filter(
        data__workflowState = 'discussion',
    )
    obj = TermspaceProgressReport.objects.create(
        tag = 'discussion',
        title = 'Alle discussion',
        description = 'Alle taken met status discussion.',
        count = query.count(),
    )
    output.append(str(obj))

    # Volkert, niet sem/med/probl/catIncompl
    query_all = TermspaceTask.objects.all()
    obj = TermspaceProgressReport.objects.create(
        tag = 'allTasks',
        title = 'Alle taken',
        description = 'Alle taken.',
        count = query_all.count(),
    )
    output.append(str(obj))

    query_open = query_all.exclude(data__workflowState = 'rejected').exclude(
        data__workflowState = 'ready for publication').exclude(
        data__workflowState = 'waiting for July publication').exclude(
        data__workflowState = 'Published').exclude(
        data__workflowState = 'published')
    obj = TermspaceProgressReport.objects.create(
        tag = 'OpenTasks',
        title = 'Open taken',
        description = 'Alle taken met status anders dan ready for publication, waiting for july publication, published.',
        count = query_open.count(),
    )
    output.append(str(obj))

    ######## Status distribution per user ########
    # Dump inbox counts per status for terminologists
    terminologists = [
        'soons',
        'mertens',
        'hielkema',
        'paiman',
        'timmer',
        'e.degroot',
        'krul',
    ]
    output = []
    for employee in terminologists:
        # Set container for total task count
        total = 0
        # Set completed statuses
        exclude = [
            'Published', 'published', 'ready for publication', 'waiting for July publication', 'rejected'
        ]
        # Get distinct statuses
        statuses = TermspaceTask.objects.all().distinct('data__workflowState').values_list('data__workflowState', flat=True)
        for status in statuses:
            # Count tasks with this status
            tasks = TermspaceTask.objects.filter(data__assignee = employee, data__workflowState = status)
            count = tasks.count()
            # Upload count to database
            output.append({
                'username' : employee,
                'status' : status,
                'count' : count,
            })
            obj = TermspaceUserReport.objects.create(
                username = employee,
                status = status,
                count = count,
            )
            output.append(str(obj))
            
            if status not in exclude:
                total += count
        # Upload total in database
        obj = TermspaceUserReport.objects.create(
            username = employee,
            status = 'total open',
            count = total,
        )
        output.append(str(obj))

    return output

@shared_task
def load_termspace_comments():
    token = None

    url = 'https://nl-prod-main.termspace.com/api/users/login'
    payload = {
        'username' : env('termspace_user'),
        'password' : env('termspace_pass'),
        }
    data = urllib.parse.urlencode(payload)
    data = data.encode('ascii')
    req = urllib.request.Request(url, data)
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read())

    token = result.get('token')

    print('Got token:',token[0:5],'.......(trunc)')

    tasks = []
    retrieved_tasks = 0

    def load_tasks(token='geen', published='true', limit=100, skip=0):
        try:
            # Per user
            url = "https://nl-prod-main.termspace.com/api/workflow/nl-edition/workflow/instances/112?projectId=57be297bc9fbcde30c573aa0&access_token={token}&excludePublished=false&viewPublished={published}&workList=asd&dontUseWorklist=true&limit={limit}&skip={skip}".format(
                token=token, 
                published=published,
                limit=limit,
                skip=skip,
            )

            req = Request(url)
            response = urlopen(req).read()
            response = json.loads(response)
            return response
        except Exception as e:
            print('Error in retrieving tasks', e)
            return None
    start = 0
    limit = 30000
    while True:
        result = load_tasks(token=token, skip=start, limit=limit, published='false')
        for item in result:
            tasks.append(item)
            
        start += limit
        if len(result) == 0: break
        # DEBUG
        # if len(tasks) > 100: break
        print('Interval: got {tasks}.'.format(tasks=len(tasks)))

    start = 0
    limit = 30000
    while True: 
        result = load_tasks(token=token, skip=start, limit=limit, published='true')
        for item in result:
            tasks.append(item)

        start += limit
        if len(result) == 0: break
        # DEBUG
        # if len(tasks) > 100: break
        print('Interval: got {tasks} tasks.'.format(tasks=len(tasks)))

    retrieved_tasks = len(tasks)

    # Add to db
    for task in tasks:
        # print('Task:',task.get('_id'))
        comments = task.get('comments',None)
        if comments:
            for comment in comments:
                # print('all:',comment)
                # print('Comment:',comment.get('text'))
                obj = TermspaceComments.objects.get_or_create(
                    concept = task.get('terminologyComponent').get('id'),
                    task_id = task.get('_id'),
                    fsn = task.get('terminologyComponent').get('name'),
                    comment = comment.get('text'),
                    time = comment.get('time'),
                    folder = task.get('folder'),
                )
                obj.status = task.get('workflowState')
                obj.assignee = comment.get('author')
                obj.save()

    print('Got',retrieved_tasks,'tasks from termspace.')

    pass