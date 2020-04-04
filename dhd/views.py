from django.shortcuts import render

# Create your views here.

# howdy/views.py
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.template.defaultfilters import linebreaksbr
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from urllib.request import urlopen, Request
import urllib.parse
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.db.models import Q
import json
from .forms import *
from mapping.models import *
from .models import *
import time
import environ

from rest_framework import viewsets
from .serializers import *
from rest_framework import views
from rest_framework.response import Response
from rest_framework.permissions import *

from snowstorm_client import Snowstorm

from django.db.models.functions import Cast

# Import environment variables
env = environ.Env(DEBUG=(bool, False))
# reading .env file
environ.Env.read_env(env.str('ENV_PATH', '.env'))

# Search termspace comments
class searchChipsoft(viewsets.ViewSet): 
    permission_classes = [IsAuthenticated]
    def retrieve(self, request, pk=None):
        term = str(pk)
        print(request)
        # Get results for searchterm        
        query = None ## Query to search for every search term
        terms = term.split(' ')
        print(request.user.username, 'Searching for:',term)
        for term in terms:
            or_query = None ## Query to search for a given term in each field
            for field_name in ['component_title']:
                q = Q(**{"%s__icontains" % field_name: term})
                if or_query is None:
                    or_query = q
                else:
                    or_query = or_query | q
            if query is None:
                query = or_query
            else:
                query = query & or_query

        print("Query:",query)

        # Search in titles
        search_results_title = MappingCodesystemComponent.objects.filter(query).order_by('-codesystem_id__id', 'component_title')
        # search_results_title = search_results_title.exclude(component_extra_dict__Actief = False)
        search_results_title = search_results_title.exclude(codesystem_id__id = 5)
        search_results_title = search_results_title.exclude(codesystem_id__id = 4)
        search_results_title = search_results_title.exclude(codesystem_id__id = 3)
        search_results_title = search_results_title.exclude(codesystem_id__id = 2)
        # print(search_results_title.count(), "results op titel")

        # Search in descriptions        
        search_results_descriptions = MappingCodesystemComponent.objects.annotate(
                            descriptions_text=Cast('descriptions', models.TextField()),
                        ).filter(descriptions_text__icontains=str(pk))
        # print(search_results_descriptions.count(), "results op termen")

        # Merge both queries
        search_results = search_results_title | search_results_descriptions
        # print(search_results.count(), "results op beide")

        # Get SNOMED results on << 'clinical finding (finding)'
        snomed_results = search_results.filter(codesystem_id__id = 1)
        # Get descendants of 'clinical finding'
        concept_clinFinding = MappingCodesystemComponent.objects.get(codesystem_id__id = 1, component_id = '404684003')#64572001
        descendants_clinFinding = json.loads(concept_clinFinding.descendants)
        print(len(descendants_clinFinding),"aantal items in clinical findings")
        # Apply filter descendants of 'clinical finding'
        snomed_results = snomed_results.filter(component_id__in=descendants_clinFinding)
        # print(snomed_results.count(), "results in << clinical finding (finding)")
        
        # Get non-snomed results
        other_results = search_results.exclude(codesystem_id__id = 1)
        # other_results = other_results.exclude(component_extra_dict__Actief = False)
        # Merge the querysets
        search_results = snomed_results | other_results

        results = []
        # if search_results.count() == 0:
        #     print('Geen resultaten')
        # else:
        #     print("Resultaat:",search_results)

        # Handle search results
        ignore_list = []
        for concept in search_results[0:15]:
            equivalent = False
            if (concept.id in ignore_list):
                print("ignored", concept.id, str(concept))
                continue
            elif (concept.codesystem_id.codesystem_title == 'Snomed'):
                # Look for diagnosethesaurus items with mapping to this snomed code
                sctid = str(concept)
                print(concept.id, sctid)
                dt_concepts = MappingCodesystemComponent.objects.filter(component_extra_dict__snomed_mapping=concept.component_id)
                if dt_concepts.exists():
                    equivalent = []
                    for dt_concept in dt_concepts:
                        equivalent.append({
                            'id' : dt_concept.id,
                            'codesystem' : dt_concept.codesystem_id.codesystem_title,
                            'code' : dt_concept.component_id,
                            'title' : dt_concept.component_title,
                            'extra' : dt_concept.component_extra_dict,
                        })
                # Check if descendants have a DT mapping or concept is DT
                dt_descendants = False
                try:
                    descendants = json.loads(concept.descendants)
                except:
                    descendants = []
                for descendant in descendants:
                    mapping_query = MappingCodesystemComponent.objects.filter(component_extra_dict__snomed_mapping=descendant)
                    if mapping_query.exists():
                        dt_descendants = True
                        break
                
            elif concept.codesystem_id.codesystem_title == 'Diagnosethesaurus':
                # Append snomed concepts that this item referred to
                sctid = str(concept)
                print(sctid)
                snomed_concepts = MappingCodesystemComponent.objects.filter(component_id=concept.component_extra_dict.get('snomed_mapping',None))
                
                if snomed_concepts.exists():
                    equivalent = []
                    for snomed_concept in snomed_concepts:
                        equivalent.append({
                            'id' : snomed_concept.id,
                            'codesystem' : snomed_concept.codesystem_id.codesystem_title,
                            'code' : snomed_concept.component_id,
                            'title' : snomed_concept.component_title,
                            'extra' : snomed_concept.component_extra_dict,
                        })
                        # ignore_list.append(concept.component_extra_dict.get('snomed_mapping',None))
                        ignore_list.append(snomed_concept.id)
                        # print("Ignore list:",ignore_list)
                # Check if descendants have a DT mapping or concept is DT
                dt_descendants = True
                descendants = None
            

            results.append({
                'id' : concept.id,
                'codesystem' : concept.codesystem_id.codesystem_title,
                'code' : concept.component_id,
                'title' : concept.component_title,
                'extra' : concept.component_extra_dict,
                'equivalent' : equivalent,
                'descendants' : descendants,
                'dt_in_descendants' : dt_descendants,
            })

        sep = " "
        context = {
            # 'searchterm' : sep.join(terms),
            # 'results_returned' : len(results),
            # 'results_total' : search_results.count(),
            'results': results,
        }
        return Response(context)

class searchChipsoftChildren(viewsets.ViewSet): 
    permission_classes = [IsAuthenticated]
    def retrieve(self, request, pk=None):
        concept = MappingCodesystemComponent.objects.get(id=pk)

        results = []
        skip = False

        if concept.codesystem_id.codesystem_title == 'Diagnosethesaurus':
            # Refer the rest of the script to the Snomed mapped concept, if it exists. If no mapping is available - return empty list.
            results = []
            skip = False
            snomedid = concept.component_extra_dict.get('snomed_mapping',False)
            if snomedid:
                try:
                    concept = MappingCodesystemComponent.objects.get(component_id=snomedid, codesystem_id_id=1)
                    children = json.loads(concept.children)
                except:
                    return Response({'children' : []})
            else:
                children = []
                skip = True
        elif concept.codesystem_id.codesystem_title == 'Snomed':
            try:
                children = json.loads(concept.children)
            except:
                children = []
                skip = True

        if skip == False:
            for concept in children:
                child_concept = MappingCodesystemComponent.objects.get(component_id=concept)
                
                try:
                    concept_children = len(json.loads(child_concept.children))
                except:
                    concept_children = 0

                equivalent = False
                if child_concept.codesystem_id.codesystem_title == 'Snomed':
                    # Look for diagnosethesaurus items with mapping to this snomed code
                    sctid = str(concept)
                    print(sctid)
                    dt_concepts = MappingCodesystemComponent.objects.filter(component_extra_dict__snomed_mapping=concept)
                    if dt_concepts.exists():
                        equivalent = []
                        for dt_concept in dt_concepts:
                            equivalent.append({
                                'id' : dt_concept.id,
                                'codesystem' : dt_concept.codesystem_id.codesystem_title,
                                'code' : dt_concept.component_id,
                                'title' : dt_concept.component_title,
                                'extra' : dt_concept.component_extra_dict,
                            })

                    # Check if descendants have a DT mapping or concept is DT
                    dt_descendants = False
                    try:
                        descendants = json.loads(child_concept.descendants)
                    except:
                        descendants = []
                    for descendant in descendants:
                        mapping_query = MappingCodesystemComponent.objects.filter(component_extra_dict__snomed_mapping=descendant)
                        if mapping_query.exists():
                            dt_descendants = True
                            print(descendant, 'true')
                            break

                results.append({
                    'id' : child_concept.id,
                    'codesystem' : child_concept.codesystem_id.codesystem_title,
                    'code' : child_concept.component_id,
                    'title' : child_concept.component_title,
                    'extra' : child_concept.component_extra_dict,
                    'equivalent' : equivalent,
                    'children' : concept_children,
                    'dt_in_descendants' : dt_descendants,
                })


        return Response({'children' : results})

class searchChipsoftParents(viewsets.ViewSet): 
    permission_classes = [IsAuthenticated]
    def retrieve(self, request, pk=None):
        concept = MappingCodesystemComponent.objects.get(id=pk)

        results = []
        skip = False

        if concept.codesystem_id.codesystem_title == 'Diagnosethesaurus':
            # Refer the rest of the script to the Snomed mapped concept, if it exists. If no mapping is available - return empty list.
            results = []
            skip = False
            snomedid = concept.component_extra_dict.get('snomed_mapping',False)
            if snomedid:
                try:
                    concept = MappingCodesystemComponent.objects.get(component_id=snomedid, codesystem_id_id=1)
                    parents = json.loads(concept.parents)
                except:
                    return Response({'parents' : []})
            else:
                parents = []
                skip = True
        elif concept.codesystem_id.codesystem_title == 'Snomed':
            try:
                parents = json.loads(concept.parents)
            except:
                parents = []
                skip = True

        if skip == False:
            for concept in parents:
                parent_concept = MappingCodesystemComponent.objects.get(component_id=concept)
                
                try:
                    concept_children = len(json.loads(parent_concept.children))
                except:
                    concept_children = 0

                equivalent = False
                if parent_concept.codesystem_id.codesystem_title == 'Snomed':
                    # Look for diagnosethesaurus items with mapping to this snomed code
                    sctid = str(concept)
                    print(sctid)
                    dt_concepts = MappingCodesystemComponent.objects.filter(component_extra_dict__snomed_mapping=concept)
                    if dt_concepts.exists():
                        equivalent = []
                        for dt_concept in dt_concepts:
                            equivalent.append({
                                'id' : dt_concept.id,
                                'codesystem' : dt_concept.codesystem_id.codesystem_title,
                                'code' : dt_concept.component_id,
                                'title' : dt_concept.component_title,
                                'extra' : dt_concept.component_extra_dict,
                            })

                    # Check if descendants have a DT mapping or concept is DT
                    dt_descendants = False
                    try:
                        descendants = json.loads(parent_concept.descendants)
                    except:
                        descendants = []
                    for descendant in descendants:
                        mapping_query = MappingCodesystemComponent.objects.filter(component_extra_dict__snomed_mapping=descendant)
                        if mapping_query.exists():
                            dt_descendants = True
                            print(descendant, 'true')
                            break

                results.append({
                    'id' : parent_concept.id,
                    'codesystem' : parent_concept.codesystem_id.codesystem_title,
                    'code' : parent_concept.component_id,
                    'title' : parent_concept.component_title,
                    'extra' : parent_concept.component_extra_dict,
                    'equivalent' : equivalent,
                    'children' : concept_children,
                    'dt_in_descendants' : dt_descendants,
                })


        return Response({'parents' : results})

class searchChipsoftConcept(viewsets.ViewSet): 
    permission_classes = [IsAuthenticated]
    def retrieve(self, request, pk=None):
        concept = MappingCodesystemComponent.objects.get(id=pk)

        equivalent = False
        if concept.codesystem_id.codesystem_title == 'Snomed':
            # Look for diagnosethesaurus items with mapping to this snomed code
            sctid = str(concept)
            print(sctid)
            dt_concepts = MappingCodesystemComponent.objects.filter(component_extra_dict__snomed_mapping=concept.component_id)
            if dt_concepts.exists():
                equivalent = []
                for dt_concept in dt_concepts:
                    equivalent.append({
                        'id' : dt_concept.id,
                        'codesystem' : dt_concept.codesystem_id.codesystem_title,
                        'code' : dt_concept.component_id,
                        'title' : dt_concept.component_title,
                        'extra' : dt_concept.component_extra_dict,
                    })


        # If snomed + 1 equivalent map: return DT. Else, continue to Snomed.
        
        elif concept.codesystem_id.codesystem_title == 'Diagnosethesaurus':
            ## Don't show equivalent items for DT items - end station
            # Append snomed concepts that this item referred to
            sctid = str(concept)
            # print(sctid)
            snomed_concepts = MappingCodesystemComponent.objects.filter(component_id=concept.component_extra_dict.get('snomed_mapping',None))
            if snomed_concepts.exists():
                equivalent = []
                for snomed_concept in snomed_concepts:
                    equivalent.append({
                        'id' : snomed_concept.id,
                        'codesystem' : snomed_concept.codesystem_id.codesystem_title,
                        'code' : snomed_concept.component_id,
                        'title' : snomed_concept.component_title,
                        'extra' : snomed_concept.component_extra_dict,
                        'dt_in_descendants' : True,
                    })


        result = {
            'id' : concept.id,
            'codesystem' : concept.codesystem_id.codesystem_title,
            'code' : concept.component_id,
            'title' : concept.component_title,
            'extra' : concept.component_extra_dict,
            'equivalent' : equivalent,
        }


        return Response(result)

class SnomedJSONTree(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def retrieve(self, request, pk=None):
        def list_children(focus):
            component = MappingCodesystemComponent.objects.get(component_id=focus)
            
            _children = []
            if component.children != None:
                for child in list(json.loads(component.children)):
                    _children.append(list_children(child))
           
            output = {
                'id' : focus,
                'name' : component.component_title,
                'children' : _children
            }
            
            return(output)

        print('Get tree for',str(pk))
        children_list = list_children(pk)

        return Response(children_list)