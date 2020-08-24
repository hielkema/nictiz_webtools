from rest_framework import serializers
import json
from .models import *
from mapping.models import *


class TermspaceCommentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "task_id", "concept", "fsn", "assignee", "comment", "folder", "time", "status")
        model = TermspaceComments


class MappingComponentSerializer(serializers.ModelSerializer):
    parents = serializers.JSONField(required=False, allow_null=True)
    children = serializers.JSONField(required=False, allow_null=True)
    ancestors = serializers.JSONField(required=False, allow_null=True)
    descendants = serializers.JSONField(required=False, allow_null=True)

    def to_representation(self, instance):
        ret = super(MappingComponentSerializer, self).to_representation(instance)
        if ret['parents'] != None: ret['parents'] = json.loads(ret['parents'])
        if ret['children'] != None: ret['children'] = json.loads(ret['children'])
        if ret['ancestors'] != None: ret['ancestors'] = json.loads(ret['ancestors'])
        if ret['descendants'] != None: ret['descendants'] = json.loads(ret['descendants'])
        return ret
    class Meta:
        model = MappingCodesystemComponent
        fields = ("component_title", "component_id", "ancestors", "parents", "children", "descendants", "descriptions")

class EclQueryResultsSerializer(serializers.ModelSerializer):
    parents = serializers.JSONField(required=False, allow_null=True)
    children = serializers.JSONField(required=False, allow_null=True)
    ancestors = serializers.JSONField(required=False, allow_null=True)
    descendants = serializers.JSONField(required=False, allow_null=True)

    def to_representation(self, instance):
        ret = super(EclQueryResultsSerializer, self).to_representation(instance)
        if ret['parents'] != None: ret['parents'] = json.loads(ret['parents'])
        if ret['children'] != None: ret['children'] = json.loads(ret['children'])
        if ret['ancestors'] != None: ret['ancestors'] = json.loads(ret['ancestors'])
        if ret['descendants'] != None: ret['descendants'] = json.loads(ret['descendants'])
        return ret

    class Meta:
        model = EclQueryResults
        fields = ("component_title", "component_id", "component_extra_dict", "ancestors", "parents", "children", "descendants")

class testEndPointSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    comments = serializers.IntegerField()
    likes = serializers.IntegerField()