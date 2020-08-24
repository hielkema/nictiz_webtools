from rest_framework import serializers
import json
from .models import *
from mapping.models import *

from rest_framework import serializers


class RootConceptSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sctid = serializers.CharField()
    fsn = serializers.CharField()

    class Meta:
        model = rootConcept
class AttributeValueSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sctid = serializers.CharField()
    fsn = serializers.CharField()

    class Meta:
        model = attributeValue
class AttributeSetSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sctid = serializers.CharField()
    fsn = serializers.CharField()
    attribute_values = AttributeValueSerializer(read_only=True, many=True)

    class Meta:
        model = attributeSet

class TemplateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    root_concept = RootConceptSerializer(read_only=True, many=False)
    attributes = AttributeSetSerializer(read_only=True, many=True)

    class Meta:
        model = template