from rest_framework import viewsets
from ..serializers import *
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework import permissions

from ..tasks import *
from ..forms import *
from ..models import *

class StatusReport(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    def list(self, request):
        print(f"[serverStatus/StatusReport list] requested")
        return Response('All systems are go', status=status.HTTP_200_OK)