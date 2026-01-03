from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import Project, Task, SubTask, Tag, Comment, Attachment
from .serializers import (
    UserSerializer, UserRegistrationSerializer, TagSerializer,
    ProjectListSerializer, ProjectDetailSerializer, ProjectCreateUpdateSerializer,
    TaskListSerializer, TaskDetailSerializer, TaskCreateUpdateSerializer,
    SubTaskSerializer, CommentSerializer, AttachmentSerializer,
    DashboardSerializer
)
from .permissions import (
    IsProjectOwner, IsProjectMember, IsTaskProjectMember,
    IsCommentAuthorOrReadOnly, IsAttachmentUploaderOrProjectMember
)
from .filters import TaskFilter, ProjectFilter


class RegisterView(APIView):
    """Vue pour l'inscription des utilisateurs"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Utilisateur créé avec succès',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les utilisateurs (lecture seule)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Retourne l'utilisateur connecté"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Met à jour le profil de l'utilisateur connecté"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet pour les tags"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet pour les projets"""
    permission_classes = [IsAuthenticated, IsProjectOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Retourne les projets où l'utilisateur est membre ou propriétaire"""
        user = self.request.user
        return Project.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProjectCreateUpdateSerializer
        return ProjectDetailSerializer
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Ajoute un membre au projet"""
        project = self.get_object()
        if project.owner != request.user:
            return Response(
                {'error': 'Seul le propriétaire peut ajouter des membres'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            project.members.add(user)
            return Response({'message': f'{user.username} ajouté au projet'})
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Retire un membre du projet"""
        project = self.get_object()
        if project.owner != request.user:
            return Response(
                {'error': 'Seul le propriétaire peut retirer des membres'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            if user == project.owner:
                return Response(
                    {'error': 'Impossible de retirer le propriétaire'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            project.members.remove(user)
            return Response({'message': f'{user.username} retiré du projet'})
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Retourne les statistiques du projet"""
        project = self.get_object()
        tasks = project.tasks.all()
        
        return Response({
            'total_tasks': tasks.count(),
            'by_status': {
                'todo': tasks.filter(status='todo').count(),
                'in_progress': tasks.filter(status='in_progress').count(),
                'review': tasks.filter(status='review').count(),
                'done': tasks.filter(status='done').count(),
            },
            'by_priority': {
                'low': tasks.filter(priority='low').count(),
                'medium': tasks.filter(priority='medium').count(),
                'high': tasks.filter(priority='high').count(),
                'urgent': tasks.filter(priority='urgent').count(),
            },
            'overdue': tasks.filter(
                due_date__lt=timezone.now(),
                status__in=['todo', 'in_progress', 'review']
            ).count(),
            'members_count': project.members.count(),
        })


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet pour les tâches"""
    permission_classes = [IsAuthenticated, IsTaskProjectMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Retourne les tâches des projets accessibles à l'utilisateur"""
        user = self.request.user
        return Task.objects.filter(
            Q(project__owner=user) | Q(project__members=user)
        ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TaskCreateUpdateSerializer
        return TaskDetailSerializer
    
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Retourne les tâches assignées à l'utilisateur"""
        tasks = self.get_queryset().filter(assignee=request.user)
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Retourne les tâches en retard"""
        tasks = self.get_queryset().filter(
            due_date__lt=timezone.now(),
            status__in=['todo', 'in_progress', 'review']
        )
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def due_today(self, request):
        """Retourne les tâches dues aujourd'hui"""
        today = timezone.now().date()
        tasks = self.get_queryset().filter(
            due_date__date=today
        )
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def due_this_week(self, request):
        """Retourne les tâches dues cette semaine"""
        today = timezone.now().date()
        week_end = today + timedelta(days=7)
        tasks = self.get_queryset().filter(
            due_date__date__range=[today, week_end]
        )
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change le statut d'une tâche"""
        task = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Task.STATUS_CHOICES):
            return Response(
                {'error': 'Statut invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = new_status
        if new_status == 'done':
            task.completed_at = timezone.now()
        else:
            task.completed_at = None
        task.save()
        
        serializer = TaskDetailSerializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assigne une tâche à un utilisateur"""
        task = self.get_object()
        user_id = request.data.get('user_id')
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                # Vérifier que l'utilisateur est membre du projet
                if user != task.project.owner and user not in task.project.members.all():
                    return Response(
                        {'error': "L'utilisateur n'est pas membre du projet"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                task.assignee = user
            except User.DoesNotExist:
                return Response(
                    {'error': 'Utilisateur non trouvé'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            task.assignee = None
        
        task.save()
        serializer = TaskDetailSerializer(task)
        return Response(serializer.data)


class SubTaskViewSet(viewsets.ModelViewSet):
    """ViewSet pour les sous-tâches"""
    serializer_class = SubTaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return SubTask.objects.filter(
            Q(task__project__owner=user) | Q(task__project__members=user)
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def toggle_complete(self, request, pk=None):
        """Bascule l'état de complétion d'une sous-tâche"""
        subtask = self.get_object()
        subtask.is_completed = not subtask.is_completed
        subtask.save()
        serializer = self.get_serializer(subtask)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet pour les commentaires"""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsCommentAuthorOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user
        return Comment.objects.filter(
            Q(task__project__owner=user) | Q(task__project__members=user)
        ).distinct()
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class AttachmentViewSet(viewsets.ModelViewSet):
    """ViewSet pour les pièces jointes"""
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated, IsAttachmentUploaderOrProjectMember]
    
    def get_queryset(self):
        user = self.request.user
        return Attachment.objects.filter(
            Q(task__project__owner=user) | Q(task__project__members=user)
        ).distinct()
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class DashboardView(APIView):
    """Vue pour le tableau de bord"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        today = timezone.now().date()
        week_end = today + timedelta(days=7)
        
        # Projets de l'utilisateur
        projects = Project.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct()
        
        # Tâches accessibles
        tasks = Task.objects.filter(
            Q(project__owner=user) | Q(project__members=user)
        ).distinct()
        
        # Statistiques
        data = {
            'total_projects': projects.count(),
            'total_tasks': tasks.count(),
            'tasks_by_status': {
                'todo': tasks.filter(status='todo').count(),
                'in_progress': tasks.filter(status='in_progress').count(),
                'review': tasks.filter(status='review').count(),
                'done': tasks.filter(status='done').count(),
            },
            'tasks_by_priority': {
                'low': tasks.filter(priority='low').count(),
                'medium': tasks.filter(priority='medium').count(),
                'high': tasks.filter(priority='high').count(),
                'urgent': tasks.filter(priority='urgent').count(),
            },
            'overdue_tasks': tasks.filter(
                due_date__lt=timezone.now(),
                status__in=['todo', 'in_progress', 'review']
            ).count(),
            'tasks_due_today': tasks.filter(due_date__date=today).count(),
            'tasks_due_this_week': tasks.filter(
                due_date__date__range=[today, week_end]
            ).count(),
            'recent_tasks': TaskListSerializer(
                tasks.order_by('-created_at')[:5], many=True
            ).data,
            'my_assigned_tasks': TaskListSerializer(
                tasks.filter(assignee=user, status__in=['todo', 'in_progress', 'review'])[:10],
                many=True
            ).data,
        }
        
        return Response(data)
