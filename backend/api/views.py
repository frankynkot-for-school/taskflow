from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Q, Count, Case, When, IntegerField
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import TaskFilter
from .models import ActivityLog, ChatConversation, ChatMessage, HierarchyRole, Attachment, Comment, InvitationStatus, Tag, Task, Workspace, WorkspaceInvitation, WorkspaceMember
from .permissions import (
    IsAdmin,
    IsAttachmentUploaderOrReadOnly,
    IsCommentAuthorOrReadOnly,
    IsTaskCreatorOrAdminOrManager,
    can_assign_by_hierarchy,
    get_workspace_role,
)
from .services import ActivityService, MistralService
from .serializers import (
    ActivityLogSerializer,
    AttachmentSerializer,
    ChatConversationDetailSerializer,
    ChatConversationListSerializer,
    ChatMessageSerializer,
    ChatSendMessageSerializer,
    CommentSerializer,
    DashboardSerializer,
    TagSerializer,
    TaskCreateUpdateSerializer,
    TaskDetailSerializer,
    TaskListSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    WorkspaceCreateSerializer,
    WorkspaceInvitationCreateSerializer,
    WorkspaceInvitationSerializer,
    WorkspaceMemberSerializer,
    WorkspaceSerializer,
)


def get_request_workspace(request):
    workspace_id = (
        request.query_params.get('workspace_id') or
        request.query_params.get('workspace') or
        request.data.get('workspace_id') or
        request.data.get('workspace')
    )
    if workspace_id:
        return Workspace.objects.filter(id=workspace_id).first() or Workspace.get_default_workspace()
    return Workspace.get_default_workspace()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Ajouter automatiquement l'utilisateur au workspace global
            workspace = Workspace.get_default_workspace()
            WorkspaceMember.objects.get_or_create(
                user=user,
                workspace=workspace,
                defaults={'role': HierarchyRole.MEMBER},
            )

            return Response(
                {
                    'message': 'Utilisateur cree avec succes',
                    'user': UserSerializer(user, context={'workspace': workspace}).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkspaceViewSet(viewsets.ModelViewSet):
    """ViewSet complet pour les workspaces (style Notion)."""
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retourne les workspaces de l'utilisateur."""
        user = self.request.user
        return Workspace.objects.filter(
            memberships__user=user
        ).distinct().select_related('owner').prefetch_related('memberships')

    def get_serializer_class(self):
        if self.action == 'create':
            return WorkspaceCreateSerializer
        return WorkspaceSerializer

    def perform_update(self, serializer):
        """Seul l'owner ou un admin peut modifier."""
        workspace = self.get_object()
        user = self.request.user
        role = workspace.get_user_role(user)
        if workspace.owner_id != user.id and role != HierarchyRole.ADMIN:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous devez être owner ou admin pour modifier ce workspace.")
        serializer.save()

    def perform_destroy(self, instance):
        """Seul l'owner peut supprimer un workspace."""
        if instance.owner_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seul le propriétaire peut supprimer ce workspace.")
        instance.delete()

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Retourne le workspace courant (par ID ou défaut)."""
        workspace = get_request_workspace(request)
        serializer = self.get_serializer(workspace)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_workspaces(self, request):
        """Liste tous les workspaces de l'utilisateur avec leur rôle."""
        workspaces = self.get_queryset()
        serializer = self.get_serializer(workspaces, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Liste les membres d'un workspace."""
        workspace = self.get_object()
        memberships = WorkspaceMember.objects.filter(
            workspace=workspace
        ).select_related('user', 'user__profile')
        serializer = WorkspaceMemberSerializer(
            memberships,
            many=True,
            context={'workspace': workspace, 'request': request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def add_member(self, request, pk=None):
        """Ajoute un membre au workspace (admin requis)."""
        workspace = self.get_object()
        request.workspace = workspace

        user_id = request.data.get('user_id')
        role = request.data.get('role', HierarchyRole.MEMBER)
        if role not in HierarchyRole.values:
            return Response({'error': 'Rôle invalide'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        membership, created = WorkspaceMember.objects.get_or_create(
            user=user,
            workspace=workspace,
            defaults={'role': role},
        )
        if not created:
            membership.role = role
            membership.save()

        serializer = WorkspaceMemberSerializer(
            membership,
            context={'workspace': workspace, 'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Quitte un workspace."""
        workspace = self.get_object()
        user = request.user

        # L'owner ne peut pas quitter son propre workspace
        if workspace.owner_id == user.id:
            return Response(
                {'error': "Le propriétaire ne peut pas quitter son workspace. Transférez la propriété ou supprimez-le."},
                status=status.HTTP_400_BAD_REQUEST
            )

        membership = WorkspaceMember.objects.filter(user=user, workspace=workspace).first()
        if not membership:
            return Response({'error': "Vous n'êtes pas membre de ce workspace."}, status=status.HTTP_400_BAD_REQUEST)

        membership.delete()
        return Response({'message': f"Vous avez quitté {workspace.name}."})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def transfer_ownership(self, request, pk=None):
        """Transfère la propriété du workspace à un autre membre."""
        workspace = self.get_object()

        if workspace.owner_id != request.user.id:
            return Response(
                {'error': "Seul le propriétaire peut transférer la propriété."},
                status=status.HTTP_403_FORBIDDEN
            )

        new_owner_id = request.data.get('user_id')
        if not new_owner_id:
            return Response({'error': "user_id requis."}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier que le nouveau owner est membre
        membership = WorkspaceMember.objects.filter(user_id=new_owner_id, workspace=workspace).first()
        if not membership:
            return Response({'error': "L'utilisateur doit être membre du workspace."}, status=status.HTTP_400_BAD_REQUEST)

        # Transférer la propriété
        workspace.owner_id = new_owner_id
        workspace.save()

        # Mettre le nouveau owner en admin
        membership.role = HierarchyRole.ADMIN
        membership.save()

        return Response({'message': "Propriété transférée avec succès."})

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsAdmin])
    def update_member_role(self, request, pk=None):
        """Met à jour le rôle d'un membre."""
        workspace = self.get_object()
        request.workspace = workspace

        user_id = request.data.get('user_id')
        new_role = request.data.get('role')

        if not user_id or not new_role:
            return Response({'error': "user_id et role requis."}, status=status.HTTP_400_BAD_REQUEST)

        if new_role not in HierarchyRole.values:
            return Response({'error': "Rôle invalide."}, status=status.HTTP_400_BAD_REQUEST)

        membership = WorkspaceMember.objects.filter(user_id=user_id, workspace=workspace).first()
        if not membership:
            return Response({'error': "Utilisateur non membre."}, status=status.HTTP_404_NOT_FOUND)

        # Empêcher de changer le rôle de l'owner
        if workspace.owner_id == int(user_id):
            return Response(
                {'error': "Impossible de changer le rôle du propriétaire."},
                status=status.HTTP_400_BAD_REQUEST
            )

        membership.role = new_role
        membership.save()

        serializer = WorkspaceMemberSerializer(
            membership,
            context={'workspace': workspace, 'request': request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated, IsAdmin])
    def remove_member(self, request, pk=None):
        """Retire un membre du workspace."""
        workspace = self.get_object()
        user_id = request.query_params.get('user_id') or request.data.get('user_id')

        if not user_id:
            return Response({'error': "user_id requis."}, status=status.HTTP_400_BAD_REQUEST)

        # Impossible de retirer l'owner
        if workspace.owner_id == int(user_id):
            return Response(
                {'error': "Impossible de retirer le propriétaire."},
                status=status.HTTP_400_BAD_REQUEST
            )

        membership = WorkspaceMember.objects.filter(user_id=user_id, workspace=workspace).first()
        if not membership:
            return Response({'error': "Utilisateur non membre."}, status=status.HTTP_404_NOT_FOUND)

        membership.delete()
        return Response({'message': "Membre retiré avec succès."})


class WorkspaceInvitationViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les invitations de workspace."""
    serializer_class = WorkspaceInvitationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retourne les invitations selon le contexte."""
        user = self.request.user
        workspace_id = self.request.query_params.get('workspace_id')

        if workspace_id:
            # Invitations d'un workspace spécifique (si admin/manager)
            return WorkspaceInvitation.objects.filter(
                workspace_id=workspace_id,
                workspace__memberships__user=user,
                workspace__memberships__role__in=[HierarchyRole.ADMIN, HierarchyRole.MANAGER]
            ).select_related('workspace', 'invited_by', 'invited_user')
        else:
            # Invitations reçues par l'utilisateur
            return WorkspaceInvitation.objects.filter(
                Q(email=user.email) | Q(invited_user=user),
                status=InvitationStatus.PENDING,
            ).select_related('workspace', 'invited_by')

    def get_serializer_class(self):
        if self.action == 'create':
            return WorkspaceInvitationCreateSerializer
        return WorkspaceInvitationSerializer

    def create(self, request, *args, **kwargs):
        """Crée une invitation (admin/manager requis)."""
        workspace_id = request.data.get('workspace_id')
        if not workspace_id:
            return Response({'error': "workspace_id requis."}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier les permissions
        membership = WorkspaceMember.objects.filter(
            user=request.user,
            workspace_id=workspace_id,
            role__in=[HierarchyRole.ADMIN, HierarchyRole.MANAGER]
        ).first()

        if not membership:
            return Response(
                {'error': "Vous devez être admin ou manager pour inviter des membres."},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Liste les invitations en attente pour l'utilisateur."""
        invitations = WorkspaceInvitation.objects.filter(
            Q(email=request.user.email) | Q(invited_user=request.user),
            status=InvitationStatus.PENDING,
        ).select_related('workspace', 'invited_by')

        # Filtrer les expirées
        valid_invitations = [inv for inv in invitations if inv.is_valid]
        serializer = self.get_serializer(valid_invitations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accepte une invitation."""
        invitation = self.get_object()

        # Vérifier que c'est bien pour cet utilisateur
        if invitation.email != request.user.email and invitation.invited_user_id != request.user.id:
            return Response(
                {'error': "Cette invitation ne vous est pas destinée."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            membership = invitation.accept(request.user)
            return Response({
                'message': f"Vous avez rejoint {invitation.workspace.name}!",
                'workspace': WorkspaceSerializer(invitation.workspace, context={'request': request}).data,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Refuse une invitation."""
        invitation = self.get_object()

        if invitation.email != request.user.email and invitation.invited_user_id != request.user.id:
            return Response(
                {'error': "Cette invitation ne vous est pas destinée."},
                status=status.HTTP_403_FORBIDDEN
            )

        invitation.decline()
        return Response({'message': "Invitation refusée."})

    @action(detail=False, methods=['get'])
    def by_token(self, request):
        """Récupère une invitation par son token."""
        token = request.query_params.get('token')
        if not token:
            return Response({'error': "Token requis."}, status=status.HTTP_400_BAD_REQUEST)

        invitation = WorkspaceInvitation.objects.filter(token=token).first()
        if not invitation:
            return Response({'error': "Invitation non trouvée."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(invitation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def resend(self, request, pk=None):
        """Renvoie une invitation (prolonge l'expiration)."""
        invitation = self.get_object()

        # Vérifier les permissions
        membership = WorkspaceMember.objects.filter(
            user=request.user,
            workspace=invitation.workspace,
            role__in=[HierarchyRole.ADMIN, HierarchyRole.MANAGER]
        ).first()

        if not membership:
            return Response(
                {'error': "Permissions insuffisantes."},
                status=status.HTTP_403_FORBIDDEN
            )

        from django.utils import timezone
        from datetime import timedelta

        invitation.expires_at = timezone.now() + timedelta(days=7)
        invitation.status = InvitationStatus.PENDING
        invitation.save()

        return Response({'message': "Invitation renvoyée."})

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """Annule une invitation."""
        invitation = self.get_object()

        # Vérifier les permissions
        membership = WorkspaceMember.objects.filter(
            user=request.user,
            workspace=invitation.workspace,
            role__in=[HierarchyRole.ADMIN, HierarchyRole.MANAGER]
        ).first()

        if not membership:
            return Response(
                {'error': "Permissions insuffisantes."},
                status=status.HTTP_403_FORBIDDEN
            )

        invitation.delete()
        return Response({'message': "Invitation annulée."})


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['workspace'] = get_request_workspace(self.request)
        return context

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True, context=self.get_serializer_context())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Change user password - requires current password for verification."""
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response(
                {'error': 'current_password et new_password sont requis'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(current_password):
            return Response(
                {'detail': 'Mot de passe actuel incorrect'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_password) < 8:
            return Response(
                {'error': 'Le mot de passe doit contenir au moins 8 caractères'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Mot de passe changé avec succès'})


    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsAdmin])
    def change_role(self, request, pk=None):
        workspace = get_request_workspace(request)
        request.workspace = workspace

        target_user = self.get_object()
        new_role = request.data.get('role')
        if new_role not in HierarchyRole.values:
            return Response(
                {'error': 'Role invalide. Choix: admin, manager, team_lead, member'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership, _ = WorkspaceMember.objects.get_or_create(
            user=target_user,
            workspace=workspace,
            defaults={'role': HierarchyRole.MEMBER},
        )
        membership.role = new_role
        membership.save()

        return Response(
            {
                'message': f'Role de {target_user.username} change en {new_role}',
                'user': UserSerializer(target_user, context={'workspace': workspace}).data,
            }
        )


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsTaskCreatorOrAdminOrManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TaskFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority']
    ordering = ['-created_at']

    def _workspace(self):
        return get_request_workspace(self.request)

    def get_queryset(self):
        workspace = self._workspace()
        user = self.request.user
        role = get_workspace_role(user, workspace)

        base_qs = Task.objects.filter(workspace=workspace).select_related(
            'assignee', 'created_by', 'parent', 'workspace'
        ).prefetch_related('tags')
        if role in (HierarchyRole.ADMIN, HierarchyRole.MANAGER):
            return base_qs

        if role == HierarchyRole.TEAM_LEAD:
            return base_qs.filter(
                Q(created_by=user)
                | Q(assignee=user)
                | Q(assignee__workspace_memberships__workspace=workspace, assignee__workspace_memberships__role__in=[HierarchyRole.TEAM_LEAD, HierarchyRole.MEMBER])
            ).distinct()

        return base_qs.filter(Q(assignee=user) | Q(created_by=user)).distinct()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['workspace'] = self._workspace()
        return context

    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return TaskCreateUpdateSerializer
        return TaskDetailSerializer

    def perform_create(self, serializer):
        workspace = self._workspace()
        WorkspaceMember.objects.get_or_create(
            user=self.request.user,
            workspace=workspace,
            defaults={'role': HierarchyRole.MEMBER},
        )
        task = serializer.save(created_by=self.request.user, workspace=workspace)
        ActivityService.log_task_created(task, self.request.user)

    @action(detail=False, methods=['get'])
    def root_tasks(self, request):
        tasks = self.get_queryset().filter(parent__isnull=True)
        serializer = TaskListSerializer(tasks, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        task = self.get_object()
        children = task.children.all()
        serializer = TaskListSerializer(children, many=True, context={'workspace': task.workspace})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        tasks = self.get_queryset().filter(assignee=request.user)
        serializer = TaskListSerializer(tasks, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        tasks = self.get_queryset().filter(
            due_date__lt=timezone.now(),
            status__in=['todo', 'in_progress', 'review'],
        )
        serializer = TaskListSerializer(tasks, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def due_today(self, request):
        today = timezone.now().date()
        tasks = self.get_queryset().filter(due_date__date=today)
        serializer = TaskListSerializer(tasks, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def due_this_week(self, request):
        today = timezone.now().date()
        week_end = today + timedelta(days=7)
        tasks = self.get_queryset().filter(due_date__date__range=[today, week_end])
        serializer = TaskListSerializer(tasks, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        task = self.get_object()
        old_status = task.status
        new_status = request.data.get('status')

        if new_status not in dict(Task.STATUS_CHOICES):
            return Response({'error': 'Statut invalide'}, status=status.HTTP_400_BAD_REQUEST)

        task.status = new_status
        task.completed_at = timezone.now() if new_status == 'done' else None
        task.save()

        ActivityService.log_status_change(task, request.user, old_status, new_status)

        serializer = TaskDetailSerializer(task, context={'workspace': task.workspace})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        task = self.get_object()
        workspace = task.workspace
        user_id = request.data.get('user_id')
        old_assignee = task.assignee

        assigner_role = get_workspace_role(request.user, workspace)
        if assigner_role == HierarchyRole.MEMBER:
            return Response({'error': 'Un member ne peut pas assigner de taches.'}, status=status.HTTP_403_FORBIDDEN)

        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'Utilisateur non trouve'}, status=status.HTTP_404_NOT_FOUND)

            if not WorkspaceMember.objects.filter(user=user, workspace=workspace).exists():
                return Response({'error': 'Utilisateur non membre du workspace'}, status=status.HTTP_400_BAD_REQUEST)

            if not can_assign_by_hierarchy(request.user, user, workspace):
                return Response({'error': 'Assignation interdite par la hierarchie des roles'}, status=status.HTTP_403_FORBIDDEN)

            task.assignee = user
        else:
            task.assignee = None

        task.save()
        ActivityService.log_assignment(task, request.user, old_assignee, task.assignee)
        serializer = TaskDetailSerializer(task, context={'workspace': workspace})
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsCommentAuthorOrReadOnly]

    def get_queryset(self):
        workspace = get_request_workspace(self.request)
        user = self.request.user
        role = get_workspace_role(user, workspace)

        base_qs = Comment.objects.filter(task__workspace=workspace)
        if role in (HierarchyRole.ADMIN, HierarchyRole.MANAGER):
            return base_qs
        return base_qs.filter(Q(task__assignee=user) | Q(task__created_by=user)).distinct()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class AttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated, IsAttachmentUploaderOrReadOnly]

    def get_queryset(self):
        workspace = get_request_workspace(self.request)
        user = self.request.user
        role = get_workspace_role(user, workspace)

        base_qs = Attachment.objects.filter(task__workspace=workspace)
        if role in (HierarchyRole.ADMIN, HierarchyRole.MANAGER):
            return base_qs
        return base_qs.filter(Q(task__assignee=user) | Q(task__created_by=user)).distinct()

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        workspace = get_request_workspace(request)
        user = request.user
        today = timezone.now().date()
        week_end = today + timedelta(days=7)
        role = get_workspace_role(user, workspace)

        tasks = Task.objects.filter(workspace=workspace)
        if role not in (HierarchyRole.ADMIN, HierarchyRole.MANAGER):
            tasks = tasks.filter(Q(assignee=user) | Q(created_by=user)).distinct()

        # Use aggregation to get all counts in a single query
        stats = tasks.aggregate(
            total_tasks=Count('id'),
            root_tasks=Count(Case(When(parent__isnull=True, then=1), output_field=IntegerField())),
            todo_count=Count(Case(When(status='todo', then=1), output_field=IntegerField())),
            in_progress_count=Count(Case(When(status='in_progress', then=1), output_field=IntegerField())),
            review_count=Count(Case(When(status='review', then=1), output_field=IntegerField())),
            done_count=Count(Case(When(status='done', then=1), output_field=IntegerField())),
            low_priority_count=Count(Case(When(priority='low', then=1), output_field=IntegerField())),
            medium_priority_count=Count(Case(When(priority='medium', then=1), output_field=IntegerField())),
            high_priority_count=Count(Case(When(priority='high', then=1), output_field=IntegerField())),
            urgent_priority_count=Count(Case(When(priority='urgent', then=1), output_field=IntegerField())),
            overdue_count=Count(Case(
                When(due_date__lt=timezone.now(), status__in=['todo', 'in_progress', 'review'], then=1),
                output_field=IntegerField()
            )),
            due_today_count=Count(Case(When(due_date__date=today, then=1), output_field=IntegerField())),
            due_this_week_count=Count(Case(
                When(due_date__date__range=[today, week_end], then=1),
                output_field=IntegerField()
            )),
        )

        recent_tasks_qs = tasks.select_related('assignee', 'created_by').prefetch_related('tags').order_by('-created_at')[:5]
        my_tasks_qs = tasks.select_related('assignee', 'created_by').prefetch_related('tags').filter(
            assignee=user, status__in=['todo', 'in_progress', 'review']
        )[:5]

        data = {
            'total_tasks': stats['total_tasks'],
            'root_tasks': stats['root_tasks'],
            'tasks_by_status': {
                'todo': stats['todo_count'],
                'in_progress': stats['in_progress_count'],
                'review': stats['review_count'],
                'done': stats['done_count'],
            },
            'tasks_by_priority': {
                'low': stats['low_priority_count'],
                'medium': stats['medium_priority_count'],
                'high': stats['high_priority_count'],
                'urgent': stats['urgent_priority_count'],
            },
            'overdue_tasks': stats['overdue_count'],
            'tasks_due_today': stats['due_today_count'],
            'tasks_due_this_week': stats['due_this_week_count'],
            'recent_tasks': recent_tasks_qs,
            'my_assigned_tasks': my_tasks_qs,
        }

        serializer = DashboardSerializer(data, context={'workspace': workspace})
        return Response(serializer.data)


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour consulter le journal d'activite."""
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['task', 'user', 'activity_type']
    ordering = ['-created_at']

    def get_queryset(self):
        workspace = get_request_workspace(self.request)
        return ActivityLog.objects.filter(workspace=workspace).select_related(
            'user', 'target_user', 'task'
        )

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Retourne les 20 dernieres activites."""
        activities = self.get_queryset()[:20]
        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)


class ChatConversationViewSet(viewsets.ModelViewSet):
    """ViewSet pour les conversations de chat."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        workspace = get_request_workspace(self.request)
        return ChatConversation.objects.filter(
            workspace=workspace,
            user=self.request.user,
            is_archived=False,
        ).prefetch_related('messages')

    def get_serializer_class(self):
        if self.action == 'list':
            return ChatConversationListSerializer
        return ChatConversationDetailSerializer

    def perform_create(self, serializer):
        workspace = get_request_workspace(self.request)
        serializer.save(
            workspace=workspace,
            user=self.request.user,
        )

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive une conversation."""
        conversation = self.get_object()
        conversation.is_archived = True
        conversation.save(update_fields=['is_archived'])
        return Response({'message': 'Conversation archivee.'})

    @action(detail=False, methods=['get'])
    def archived(self, request):
        """Liste les conversations archivees."""
        workspace = get_request_workspace(request)
        conversations = ChatConversation.objects.filter(
            workspace=workspace,
            user=request.user,
            is_archived=True,
        )
        serializer = ChatConversationListSerializer(conversations, many=True)
        return Response(serializer.data)


class ChatMessageView(APIView):
    """Vue pour envoyer un message au chatbot."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatSendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        workspace = get_request_workspace(request)
        user_message = serializer.validated_data['message']
        conversation_id = serializer.validated_data.get('conversation_id')

        # Recuperer ou creer la conversation
        if conversation_id:
            try:
                conversation = ChatConversation.objects.get(
                    id=conversation_id,
                    workspace=workspace,
                    user=request.user,
                )
            except ChatConversation.DoesNotExist:
                return Response(
                    {'error': 'Conversation non trouvee.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            conversation = ChatConversation.objects.create(
                workspace=workspace,
                user=request.user,
            )

        # Envoyer le message a Mistral
        try:
            service = MistralService()
            result = service.chat(conversation, user_message)

            if result['success']:
                return Response({
                    'conversation_id': conversation.id,
                    'message': ChatMessageSerializer(result['message']).data,
                    'tokens_used': result.get('tokens_used'),
                    'user_message_id': result['message'].id,
                })
            else:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            import logging
            logger = logging.getLogger('django')
            logger.error(f"Chat error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Une erreur est survenue. Veuillez reessayer.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

