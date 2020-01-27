from rest_framework import serializers
from .models import *


class TermspaceCommentSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "task_id", "concept", "fsn", "assignee", "comment", "folder", "time", "status")
        model = TermspaceComments

class testEndPointSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    comments = serializers.IntegerField()
    likes = serializers.IntegerField()