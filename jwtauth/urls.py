from django.urls import path
from .views import registration, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', registration, name='register'),
    path(r'token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path(r'refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path(r'permissions/', permissions, name='permissions'),
]