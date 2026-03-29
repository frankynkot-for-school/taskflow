from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import (
    ActivityLog,
    Attachment,
    ChatConversation,
    ChatMessage,
    Comment,
    HierarchyRole,
    InvitationStatus,
    Tag,
    Task,
    UserProfile,
    Workspace,
    WorkspaceInvitation,
    WorkspaceMember,
    WorkspaceType,
)


def get_workspace_for_serializer(serializer):
    workspace = serializer.context.get('workspace')
    if workspace:
        return workspace
    return Workspace.get_default_workspace()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio']


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    role_label = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'role_label',
        ]
        read_only_fields = ['id']

    def _get_membership(self, obj):
        workspace = get_workspace_for_serializer(self)
        return WorkspaceMember.objects.filter(user=obj, workspace=workspace).first()

    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'.strip() or obj.username

    def get_role(self, obj):
        membership = self._get_membership(obj)
        return membership.role if membership else HierarchyRole.MEMBER

    def get_role_label(self, obj):
        membership = self._get_membership(obj)
        if not membership:
            return HierarchyRole(HierarchyRole.MEMBER).label
        return HierarchyRole(membership.role).label


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': 'Les mots de passe ne correspondent pas.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source='user',
        queryset=User.objects.all(),
        write_only=True,
        required=False,
    )
    role_label = serializers.SerializerMethodField()

    class Meta:
        model = WorkspaceMember
        fields = ['id', 'workspace', 'user', 'user_id', 'role', 'role_label', 'joined_at']
        read_only_fields = ['id', 'joined_at', 'user']

    def get_role_label(self, obj):
        return HierarchyRole(obj.role).label


class WorkspaceSerializer(serializers.ModelSerializer):
    """Serializer complet pour les workspaces (style Notion)."""
    members_count = serializers.SerializerMethodField()
    tasks_count = serializers.SerializerMethodField()
    owner = UserSerializer(read_only=True)
    user_role = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    workspace_type_label = serializers.CharField(
        source='get_workspace_type_display',
        read_only=True,
    )

    class Meta:
        model = Workspace
        fields = [
            'id',
            'name',
            'description',
            'icon',
            'color',
            'workspace_type',
            'workspace_type_label',
            'owner',
            'is_default',
            'created_at',
            'updated_at',
            'members_count',
            'tasks_count',
            'user_role',
            'is_owner',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']

    def get_members_count(self, obj):
        return obj.memberships.count()

    def get_tasks_count(self, obj):
        return obj.tasks.count()

    def get_user_role(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_user_role(request.user)
        return None

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.owner_id == request.user.id
        return False


class WorkspaceCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de workspace."""

    class Meta:
        model = Workspace
        fields = ['id', 'name', 'description', 'icon', 'color', 'workspace_type']
        read_only_fields = ['id']

    def create(self, validated_data):
        user = self.context['request'].user
        workspace = Workspace.objects.create(
            **validated_data,
            owner=user,
        )
        # Ajouter le créateur comme admin
        WorkspaceMember.objects.create(
            user=user,
            workspace=workspace,
            role=HierarchyRole.ADMIN,
        )
        return workspace


class WorkspaceInvitationSerializer(serializers.ModelSerializer):
    """Serializer pour les invitations de workspace."""
    workspace = WorkspaceSerializer(read_only=True)
    workspace_id = serializers.PrimaryKeyRelatedField(
        source='workspace',
        queryset=Workspace.objects.all(),
        write_only=True,
    )
    invited_by = UserSerializer(read_only=True)
    invited_user = UserSerializer(read_only=True)
    role_label = serializers.CharField(
        source='get_role_display',
        read_only=True,
    )
    status_label = serializers.CharField(
        source='get_status_display',
        read_only=True,
    )
    is_valid = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = WorkspaceInvitation
        fields = [
            'id',
            'workspace',
            'workspace_id',
            'email',
            'invited_by',
            'invited_user',
            'role',
            'role_label',
            'status',
            'status_label',
            'token',
            'message',
            'created_at',
            'expires_at',
            'accepted_at',
            'is_valid',
            'is_expired',
        ]
        read_only_fields = [
            'id',
            'token',
            'invited_by',
            'invited_user',
            'status',
            'created_at',
            'accepted_at',
        ]


class WorkspaceInvitationCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une invitation."""
    workspace_id = serializers.PrimaryKeyRelatedField(
        source='workspace',
        queryset=Workspace.objects.all(),
    )

    class Meta:
        model = WorkspaceInvitation
        fields = ['workspace_id', 'email', 'role', 'message']

    def validate_email(self, value):
        """Vérifie que l'email n'est pas déjà membre."""
        workspace = self.initial_data.get('workspace_id')
        if workspace:
            try:
                workspace_obj = Workspace.objects.get(id=workspace)
                user = User.objects.filter(email=value).first()
                if user and workspace_obj.is_member(user):
                    raise serializers.ValidationError(
                        "Cet utilisateur est déjà membre de ce workspace."
                    )
            except Workspace.DoesNotExist:
                pass
        return value

    def validate(self, attrs):
        # Vérifier qu'il n'y a pas déjà une invitation en attente
        workspace = attrs.get('workspace')
        email = attrs.get('email')

        existing = WorkspaceInvitation.objects.filter(
            workspace=workspace,
            email=email,
            status=InvitationStatus.PENDING,
        ).exists()

        if existing:
            raise serializers.ValidationError({
                'email': "Une invitation est déjà en attente pour cet email."
            })

        return attrs

    def create(self, validated_data):
        from django.utils import timezone
        from datetime import timedelta

        validated_data['invited_by'] = self.context['request'].user
        validated_data['token'] = WorkspaceInvitation.generate_token()
        validated_data['expires_at'] = timezone.now() + timedelta(days=7)

        # Si l'utilisateur existe déjà, le lier
        email = validated_data.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            validated_data['invited_user'] = user

        return super().create(validated_data)


class TagSerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'task_count']

    def get_task_count(self, obj):
        return obj.tasks.count()


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'task', 'author', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'author']

    def get_author(self, obj):
        workspace = obj.task.workspace
        return UserSerializer(obj.author, context={'workspace': workspace}).data


class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = ['id', 'task', 'file', 'file_name', 'file_size', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at', 'uploaded_by']

    def get_uploaded_by(self, obj):
        workspace = obj.task.workspace
        return UserSerializer(obj.uploaded_by, context={'workspace': workspace}).data

    def get_file_name(self, obj):
        return obj.file.name.split('/')[-1] if obj.file else None

    def get_file_size(self, obj):
        try:
            return obj.file.size
        except Exception:
            return None


class TaskChildSerializer(serializers.ModelSerializer):
    assignee = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'status',
            'priority',
            'assignee',
            'due_date',
            'created_at',
            'children_count',
        ]

    def get_assignee(self, obj):
        if not obj.assignee:
            return None
        return UserSerializer(obj.assignee, context={'workspace': obj.workspace}).data

    def get_children_count(self, obj):
        return obj.children.count()


class TaskListSerializer(serializers.ModelSerializer):
    assignee = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    children_count = serializers.SerializerMethodField()
    children_completed = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    parent_title = serializers.CharField(source='parent.title', read_only=True, default=None)
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'workspace',
            'workspace_name',
            'parent',
            'parent_title',
            'assignee',
            'created_by',
            'priority',
            'status',
            'tags',
            'due_date',
            'created_at',
            'children_count',
            'children_completed',
            'comments_count',
            'progress',
        ]

    def get_assignee(self, obj):
        if not obj.assignee:
            return None
        return UserSerializer(obj.assignee, context={'workspace': obj.workspace}).data

    def get_created_by(self, obj):
        return UserSerializer(obj.created_by, context={'workspace': obj.workspace}).data

    def get_children_count(self, obj):
        return obj.children.count()

    def get_children_completed(self, obj):
        return obj.children.filter(status='done').count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_progress(self, obj):
        total = obj.children.count()
        if total == 0:
            return 100 if obj.status == 'done' else 0
        completed = obj.children.filter(status='done').count()
        return int((completed / total) * 100)


class TaskDetailSerializer(serializers.ModelSerializer):
    assignee = serializers.SerializerMethodField()
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assignee',
        write_only=True,
        required=False,
        allow_null=True,
    )
    created_by = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source='tags',
        many=True,
        write_only=True,
        required=False,
    )
    children = TaskChildSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()
    parent_title = serializers.CharField(source='parent.title', read_only=True, default=None)
    workspace_name = serializers.CharField(source='workspace.name', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'workspace',
            'workspace_name',
            'parent',
            'parent_title',
            'assignee',
            'assignee_id',
            'priority',
            'status',
            'tags',
            'tag_ids',
            'due_date',
            'created_by',
            'created_at',
            'updated_at',
            'completed_at',
            'children',
            'comments',
            'attachments',
            'progress',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_assignee(self, obj):
        if not obj.assignee:
            return None
        return UserSerializer(obj.assignee, context={'workspace': obj.workspace}).data

    def get_created_by(self, obj):
        return UserSerializer(obj.created_by, context={'workspace': obj.workspace}).data

    def get_progress(self, obj):
        total = obj.children.count()
        if total == 0:
            return 100 if obj.status == 'done' else 0
        completed = obj.children.filter(status='done').count()
        return int((completed / total) * 100)


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source='tags',
        many=True,
        required=False,
    )

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'workspace',
            'parent',
            'assignee',
            'priority',
            'status',
            'tag_ids',
            'due_date',
        ]
        read_only_fields = ['id', 'workspace']

    def validate(self, attrs):
        workspace = attrs.get('workspace') or Workspace.get_default_workspace()
        parent = attrs.get('parent')
        assignee = attrs.get('assignee')

        if parent and parent.workspace_id != workspace.id:
            raise serializers.ValidationError({'parent': 'Le parent doit appartenir au meme workspace.'})

        if assignee and not WorkspaceMember.objects.filter(user=assignee, workspace=workspace).exists():
            raise serializers.ValidationError({'assignee': 'L\'assigne doit etre membre du workspace.'})

        return attrs

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        validated_data['created_by'] = self.context['request'].user
        validated_data['workspace'] = validated_data.get('workspace') or Workspace.get_default_workspace()
        task = Task.objects.create(**validated_data)
        task.tags.set(tags)
        return task

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if tags is not None:
            instance.tags.set(tags)
        instance.save()
        return instance


class DashboardSerializer(serializers.Serializer):
    total_tasks = serializers.IntegerField()
    root_tasks = serializers.IntegerField()
    tasks_by_status = serializers.DictField()
    tasks_by_priority = serializers.DictField()
    overdue_tasks = serializers.IntegerField()
    tasks_due_today = serializers.IntegerField()
    tasks_due_this_week = serializers.IntegerField()
    recent_tasks = TaskListSerializer(many=True)
    my_assigned_tasks = TaskListSerializer(many=True)


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer pour le journal d'activite."""
    user = UserSerializer(read_only=True)
    target_user = UserSerializer(read_only=True)
    activity_type_label = serializers.CharField(
        source='get_activity_type_display',
        read_only=True,
    )

    class Meta:
        model = ActivityLog
        fields = [
            'id',
            'workspace',
            'task',
            'task_title',
            'user',
            'activity_type',
            'activity_type_label',
            'old_value',
            'new_value',
            'target_user',
            'created_at',
        ]
        read_only_fields = fields


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer pour les messages de chat."""

    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'role',
            'content',
            'created_at',
            'tokens_used',
        ]
        read_only_fields = fields


class ChatConversationListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des conversations."""
    messages_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatConversation
        fields = [
            'id',
            'title',
            'created_at',
            'updated_at',
            'is_archived',
            'messages_count',
            'last_message',
        ]

    def get_messages_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last = obj.messages.last()
        if last:
            return {
                'role': last.role,
                'content': last.content[:100] + ('...' if len(last.content) > 100 else ''),
                'created_at': last.created_at,
            }
        return None


class ChatConversationDetailSerializer(serializers.ModelSerializer):
    """Serializer pour le detail d'une conversation."""
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatConversation
        fields = [
            'id',
            'workspace',
            'title',
            'created_at',
            'updated_at',
            'is_archived',
            'messages',
        ]
        read_only_fields = ['id', 'workspace', 'created_at', 'updated_at']


class ChatSendMessageSerializer(serializers.Serializer):
    """Serializer pour envoyer un message."""
    message = serializers.CharField(max_length=4000)
    conversation_id = serializers.IntegerField(required=False)

