# nictiz_webtools
This repository contains several online tools made available by Nictiz (nictiz.nl).

- Simple ATC/g-standaard medication lookup: requires proprietary source files from z-index.nl.
- Snomed list generators (build_tree & build_tree_excel): two tools to create user-friendly Snomed lists from Snowstorm. Requires a Snowstorm server.
- Mapping tool<br>
This is a crude start to a very flexible mapping tool. The tool is at proof-of-concept level, but functional. The tool is under heavy development. Every component runs in a docker container, with volumes for persistance. Access to the production environment is controlled by a reverse proxy Nginx with letsencrypt companion container, which needs access to ports 80 and 443. <br>
At this point it supports 1-n mappings from any codesystem to any codesystem. The admin tools are still limited, but the user workflow is very usable at this point.
## Getting started
- Clone repo
- Setup your .env file (template in .env-template)
- Start dev environment with docker-compose up
- Run python manage.py makemigrations and python manage.py migrate in the python container
- Run python manage.py createsuperuser in python container
- Run python manage.py collectstatic, confirm 'yes', in python container
- In /admin/, create groups mentioned below under 'With a fresh DB'
- In /admin/mapping/, create codesystems, mapping, statuses for each project.
- For mapping Snomed (snomed.nl), open /mapping/update_snomed/ to import Snomed into a chosen codesystem. Each Snomed concept is imported as a 'component' (work in progress, functional)
- For mapping NHG (nhg.nl), open /mapping/update_nhg/ to import NHG Excel tables into a chosen codesystem. These NHG tables are proprietary, and need to be obtained. They can be placed in /mapping/resources/nhg/. Each table requires custom code, an example for 'Verrichtingen' is present in the repository. Each line is imported as a 'component' (work in progress, functional).
- After loading at least two terminology systems, mapping tasks can be created from /mapping/task_create/. You can either supply a list of unique ID's in the text field (one row per ID), or create tasks for each component from the chosen codesystem. If a task already exists for a component, it will be left as is.
- Users with group membership 'mapping | create tasks', will have a link to the task manager on the project home page.
- Start production environment with docker-compose -f prod.yml up
- the shell script 'update' in the root directory will pull the latest changes from the current Git branch and restart the production environment.

## With a fresh DB:

### Create groups: (without ')
- 'ATC lookup'                      # Access to the medication ATC/g-standaard lookup module
- 'HTML tree'                       # Access to the Snomed list generators
- 'mapping | access'                # Access to the mapping tool - not in use
- 'mapping | edit mapping'          # Edit mappings, this enables changing and adding mappings
- 'mapping | view tasks'            # View tasks in projects
- 'mapping | create tasks'          # Create tasks through CSV entry
- 'mapping | change task status'    
- 'mapping | place comments'        
- 'mapping | admin codesystems'     # Creating codesystems, loading data into codesystems
- 'mapping | audit'                 # Create audit reports on mapping rules
- 'mapping | project statistics'    # Show in-depth project statistics on project page


### Permission check in template:
{% if 'mapping | edit mapping' in permissions %}
### Permission check in class-based view:

class AjaxTargetSearch(UserPassesTestMixin,TemplateView):  # UserPassesTestMixin needs to be first!
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        # return self.request.user.has_perm('Build_Tree.make_taskRecord') # Check for permission
        return self.request.user.groups.filter(name='AJAX lookup').exists() # Check for group membership
### Render an error page
except Exception as e:
    return render(request, 'mapping/error.html', {
    'page_title': 'Error',
    'error_text': 'Mogelijk probeer je een taak te openen die niet bestaat.',
    'exception' : e,
    })

### .env file
Template can be found in .env-example