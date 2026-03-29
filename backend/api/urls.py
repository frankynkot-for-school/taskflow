from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    ActivityLogViewSet, ChatConversationViewSet, ChatMessageView, RegisterView, WorkspaceViewSet, WorkspaceInvitationViewSet,
    UserViewSet, TagViewSet, TaskViewSet, CommentViewSet, AttachmentViewSet, DashboardView
)

# Configuration du router DRF
router = DefaultRouter()
router.register(r'workspaces', WorkspaceViewSet, basename='workspace')
router.register(r'invitations', WorkspaceInvitationViewSet, basename='invitation')
router.register(r'users', UserViewSet, basename='user')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'attachments', AttachmentViewSet, basename='attachment')
router.register(r'activities', ActivityLogViewSet, basename='activity')
router.register(r'chat/conversations', ChatConversationViewSet, basename='chat-conversation')

urlpatterns = [
    # Routes du router
    path('', include(router.urls)),
    
    # Authentification JWT
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='auth-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='auth-verify'),
    
    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    # Chat
    path('chat/send/', ChatMessageView.as_view(), name='chat-send'),
]
