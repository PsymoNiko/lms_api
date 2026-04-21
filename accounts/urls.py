from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .site_admin_views import SiteAdminOverviewView
from .views import (
    AvatarUpdateView,
    CurrentUserMeView,
    LogoutView,
    ProfileView,
    RegisterView,
    UserViewSet,
)

urlpatterns = [
    # Auth Endpoints
    path('api/v1/login/', TokenObtainPairView.as_view(), name='login'),
    path('api/v1/register/', RegisterView.as_view(), name='register'),
    path(
        'api/v1/auth/register/',
        RegisterView.as_view(),
        name='auth_register',
    ),
    path('api/v1/refresh-token/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/logout/', LogoutView.as_view(), name='logout'),

    path('api/v1/me/', CurrentUserMeView.as_view(), name='me'),

    path(
        'api/v1/admin/overview/',
        SiteAdminOverviewView.as_view(),
        name='site_admin_overview',
    ),

    # Profile Endpoint (For the logged-in user)
    path('api/v1/profile/', ProfileView.as_view(), name='profile'),

    # User Management CRUD (UserViewSet)
    path('api/v1/users/', UserViewSet.as_view({
        'get': 'list',
        'post': 'create',
    }), name='users'),

    path('api/v1/users/<int:pk>/', UserViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='user_detail'),

    path('api/v1/profile/avatar/', AvatarUpdateView.as_view(), name='update-avatar'),
]
