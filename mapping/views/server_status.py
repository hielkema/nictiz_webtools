from rest_framework import viewsets
from ..serializers import *
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework import permissions

from time import time

from ..tasks import *
from ..forms import *
from ..models import *

class StatusReport(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    def list(self, request):
        print(f"[serverStatus/StatusReport list] requested @ {time.strftime('%c')}")
        for key, value in request.headers.items():
            print(f"[serverStatus/StatusReport list] {key} : {value}")
        print(f"[serverStatus/StatusReport list] {request.data}")
        return Response('All systems are go', status=418)