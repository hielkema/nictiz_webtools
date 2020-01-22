from django.shortcuts import render

# Create your views here.

# howdy/views.py
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponse
from django.template.defaultfilters import linebreaksbr
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from urllib.request import urlopen, Request
import urllib.parse
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.db.models import Q
import json
from .forms import *
from .models import *
import time
import environ
# from atc_lookup.tasks import send_post_signup_email

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))

# Create your views here.
class SearchcommentsPageView(UserPassesTestMixin, TemplateView):
    '''
    Class used search comments.
    Only usable with Snomed tree view rights
    '''
    def handle_no_permission(self):
        return redirect('login')
    def test_func(self):
        return self.request.user.groups.filter(name='HTML tree').exists()

    def get(self, request, **kwargs):
        context = {}
        return render(request, 'termspace/searchcomments.html', context=context)
    def post(self, request, **kwargs):
        term = request.POST.get('term')

        # Get results for searchterm        
        query = None ## Query to search for every search term
        terms = term.split(' ')
        print('Searching for:',term)
        for term in terms:
            or_query = None ## Query to search for a given term in each field
            for field_name in ['comment', 'assignee', 'fsn', 'folder']:
                q = Q(**{"%s__icontains" % field_name: term})
                if or_query is None:
                    or_query = q
                else:
                    or_query = or_query | q
            if query is None:
                query = or_query
            else:
                query = query & or_query

        # results = comments_found = TermspaceComments.objects.annotate(search=SearchVector('comment',),).filter(search__icontains=term)        
        comments_found = TermspaceComments.objects.filter(
                            query
                        )
        print(query)
        results = []
        if comments_found.count() == 0:
            print('Geen resultaten')
        for comment in comments_found:
            results.append({
                'id' : comment.concept,
                'author' : comment.assignee,
                'folder' : comment.folder,
                'status' : comment.status,
                'comment' : comment.comment,
                'fsn' : comment.fsn,
            })

        # print('---------')

        sep = " "
        context = {
            'searchterm' : sep.join(terms),
            'results': results,
            'num_results' : len(results),
        }

        return render(request, 'termspace/searchcomments.html', context=context)