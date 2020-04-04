from django.contrib.auth import get_user_model
from rest_framework import permissions
from rest_framework import response, decorators, permissions, status, views, viewsets
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserCreateSerializer
import json

User = get_user_model()

@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.AllowAny])
def registration(request):
    serializer = UserCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return response.Response(serializer.errors, status.HTTP_400_BAD_REQUEST)        
    user = serializer.save()
    refresh = RefreshToken.for_user(user)
    res = {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    return response.Response(res, status.HTTP_201_CREATED)

@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def permissions(request):
    permissions = []
    for item in request.user.user_permissions.all():
        permissions.append(str(item))
    groups = []
    for item in request.user.groups.all():
        groups.append(str(item))
    return response.Response({
        'id' : request.user.id,
        'username' : request.user.username,
        'details' : {
            'first_name' : request.user.first_name,
            'last_name' : request.user.first_name,
            'email' : request.user.email,
        },
        'permissions' : permissions,
        'groups' : groups,
    })
