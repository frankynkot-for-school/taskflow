from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Project, Task, SubTask, Tag, Comment, Attachment


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les utilisateurs"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = ['id']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription des utilisateurs"""
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Les mots de passe ne correspondent pas."
            })
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class TagSerializer(serializers.ModelSerializer):
    """Serializer pour les tags"""
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'task_count']
    
    def get_task_count(self, obj):
        return obj.tasks.count()


class SubTaskSerializer(serializers.ModelSerializer):
    """Serializer pour les sous-tâches"""
    
    class Meta:
        model = SubTask
        fields = ['id', 'title', 'is_completed', 'created_at']
        read_only_fields = ['id', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    """Serializer pour les commentaires"""
    author = UserSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='author',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Comment
        fields = ['id', 'task', 'author', 'author_id', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'author']


class AttachmentSerializer(serializers.ModelSerializer):
    """Serializer pour les pièces jointes"""
    uploaded_by = UserSerializer(read_only=True)
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = Attachment
        fields = ['id', 'task', 'file', 'file_name', 'file_size', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at', 'uploaded_by']
    
    def get_file_name(self, obj):
        return obj.file.name.split('/')[-1] if obj.file else None
    
    def get_file_size(self, obj):
        try:
            return obj.file.size
        except:
            return None


class TaskListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des tâches"""
    assignee = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    subtasks_count = serializers.SerializerMethodField()
    subtasks_completed = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'project', 'assignee', 'priority', 'status', 
            'tags', 'due_date', 'created_at', 'subtasks_count', 
            'subtasks_completed', 'comments_count', 'progress'
        ]
    
    def get_subtasks_count(self, obj):
        return obj.subtasks.count()
    
    def get_subtasks_completed(self, obj):
        return obj.subtasks.filter(is_completed=True).count()
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def get_progress(self, obj):
        total = obj.subtasks.count()
        if total == 0:
            return 100 if obj.status == 'done' else 0
        completed = obj.subtasks.filter(is_completed=True).count()
        return int((completed / total) * 100)


class TaskDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une tâche"""
    assignee = UserSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assignee',
        write_only=True,
        required=False,
        allow_null=True
    )
    created_by = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source='tags',
        many=True,
        write_only=True,
        required=False
    )
    subtasks = SubTaskSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'project', 'assignee', 'assignee_id',
            'priority', 'status', 'tags', 'tag_ids', 'due_date', 'created_by',
            'created_at', 'updated_at', 'completed_at', 'subtasks', 
            'comments', 'attachments', 'progress'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_progress(self, obj):
        total = obj.subtasks.count()
        if total == 0:
            return 100 if obj.status == 'done' else 0
        completed = obj.subtasks.filter(is_completed=True).count()
        return int((completed / total) * 100)


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour création/modification de tâche"""
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source='tags',
        many=True,
        required=False
    )
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'project', 'assignee',
            'priority', 'status', 'tag_ids', 'due_date'
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        validated_data['created_by'] = self.context['request'].user
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


class ProjectListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des projets"""
    owner = UserSerializer(read_only=True)
    tasks_count = serializers.SerializerMethodField()
    tasks_completed = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'owner', 'created_at', 
            'tasks_count', 'tasks_completed', 'members_count', 'progress'
        ]
    
    def get_tasks_count(self, obj):
        return obj.tasks.count()
    
    def get_tasks_completed(self, obj):
        return obj.tasks.filter(status='done').count()
    
    def get_members_count(self, obj):
        return obj.members.count()
    
    def get_progress(self, obj):
        total = obj.tasks.count()
        if total == 0:
            return 0
        completed = obj.tasks.filter(status='done').count()
        return int((completed / total) * 100)


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un projet"""
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='members',
        many=True,
        write_only=True,
        required=False
    )
    tasks = TaskListSerializer(many=True, read_only=True)
    tasks_count = serializers.SerializerMethodField()
    tasks_by_status = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'owner', 'members', 'member_ids',
            'created_at', 'updated_at', 'tasks', 'tasks_count', 
            'tasks_by_status', 'progress'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']
    
    def get_tasks_count(self, obj):
        return obj.tasks.count()
    
    def get_tasks_by_status(self, obj):
        return {
            'todo': obj.tasks.filter(status='todo').count(),
            'in_progress': obj.tasks.filter(status='in_progress').count(),
            'review': obj.tasks.filter(status='review').count(),
            'done': obj.tasks.filter(status='done').count(),
        }
    
    def get_progress(self, obj):
        total = obj.tasks.count()
        if total == 0:
            return 0
        completed = obj.tasks.filter(status='done').count()
        return int((completed / total) * 100)


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour création/modification de projet"""
    member_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='members',
        many=True,
        required=False
    )
    
    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'member_ids']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        members = validated_data.pop('members', [])
        validated_data['owner'] = self.context['request'].user
        project = Project.objects.create(**validated_data)
        project.members.set(members)
        # Ajouter automatiquement le propriétaire comme membre
        project.members.add(validated_data['owner'])
        return project
    
    def update(self, instance, validated_data):
        members = validated_data.pop('members', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if members is not None:
            instance.members.set(members)
            # S'assurer que le propriétaire reste membre
            instance.members.add(instance.owner)
        instance.save()
        return instance


class DashboardSerializer(serializers.Serializer):
    """Serializer pour le tableau de bord"""
    total_projects = serializers.IntegerField()
    total_tasks = serializers.IntegerField()
    tasks_by_status = serializers.DictField()
    tasks_by_priority = serializers.DictField()
    overdue_tasks = serializers.IntegerField()
    tasks_due_today = serializers.IntegerField()
    tasks_due_this_week = serializers.IntegerField()
    recent_tasks = TaskListSerializer(many=True)
    my_assigned_tasks = TaskListSerializer(many=True)
