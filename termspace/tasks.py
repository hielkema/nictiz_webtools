# Create your tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .models import *
import time, json
from urllib.request import urlopen, Request
import urllib.parse
import environ

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))

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

    retrieved_tasks = len(tasks)

    # Add to db
    for task in tasks:
        print('Task:',task.get('_id'))
        for comment in task.get('comments',{}):
            # print('all:',comment)
            # print('Comment:',comment.get('text'))
            obj = TermspaceComments.objects.get_or_create(
                concept = task.get('terminologyComponent').get('id'),
                task_id = task.get('_id'),
                fsn = task.get('terminologyComponent').get('name'),
                assignee = comment.get('author'),
                comment = comment.get('text'),
                time = comment.get('time'),
                folder = task.get('folder'),
                status = task.get('workflowState'),
            )
    print('Got',retrieved_tasks,'tasks from termspace.')

    pass