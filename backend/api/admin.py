from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import ActivityLog, Attachment, ChatConversation, ChatMessage, Comment, HierarchyRole, Tag, Task, UserProfile, Workspace, WorkspaceMember


admin.site.unregister(User)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil'


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_workspace_role', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    inlines = [UserProfileInline]

    def get_workspace_role(self, obj):
        workspace = Workspace.get_default_workspace()
        membership = WorkspaceMember.objects.filter(user=obj, workspace=workspace).first()
        if not membership:
            return HierarchyRole.MEMBER
        return membership.role

    get_workspace_role.short_description = 'Role workspace'


class WorkspaceMemberInline(admin.TabularInline):
    model = WorkspaceMember
    extra = 0
    fields = ['user', 'role', 'joined_at']
    readonly_fields = ['joined_at']


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at', 'updated_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [WorkspaceMemberInline]


@admin.register(WorkspaceMember)
class WorkspaceMemberAdmin(admin.ModelAdmin):
    list_display = ['workspace', 'user', 'role', 'joined_at']
    list_filter = ['workspace', 'role', 'joined_at']
    search_fields = ['workspace__name', 'user__username', 'user__email']
    readonly_fields = ['joined_at']


class ChildTaskInline(admin.TabularInline):
    model = Task
    fk_name = 'parent'
    extra = 0
    fields = ['title', 'status', 'priority', 'assignee', 'due_date']
    readonly_fields = ['created_at']
    show_change_link = True
    verbose_name = 'Sous-tache'
    verbose_name_plural = 'Sous-taches'


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ['author', 'created_at']


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ['uploaded_by', 'uploaded_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'workspace', 'parent', 'status', 'priority', 'assignee', 'due_date', 'created_at']
    list_filter = ['workspace', 'status', 'priority', 'created_at', 'due_date']
    search_fields = ['title', 'description', 'assignee__username']
    filter_horizontal = ['tags']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'created_by']
    list_editable = ['status', 'priority']
    date_hierarchy = 'created_at'
    inlines = [ChildTaskInline, CommentInline, AttachmentInline]

    fieldsets = (
        ('Informations generales', {'fields': ('workspace', 'title', 'description', 'parent')}),
        ('Assignation et statut', {'fields': ('assignee', 'status', 'priority', 'tags')}),
        ('Dates', {'fields': ('due_date', 'created_at', 'updated_at', 'completed_at')}),
        ('Cree par', {'fields': ('created_by',), 'classes': ('collapse',)}),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            if not obj.workspace_id:
                obj.workspace = Workspace.get_default_workspace()
        super().save_model(request, obj, form, change)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'tasks_count']
    search_fields = ['name']

    def tasks_count(self, obj):
        return obj.tasks.count()

    tasks_count.short_description = 'Taches associees'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'author', 'short_content', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['content', 'author__username', 'task__title']
    readonly_fields = ['created_at', 'updated_at']

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    short_content.short_description = 'Contenu'


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['task', 'file', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at', 'uploaded_by']
    search_fields = ['task__title', 'uploaded_by__username']
    readonly_fields = ['uploaded_at']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'workspace', 'task_title', 'user', 'activity_type', 'created_at']
    list_filter = ['workspace', 'activity_type', 'created_at']
    search_fields = ['task_title', 'user__username']
    readonly_fields = ['created_at']


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ['role', 'content', 'tokens_used', 'created_at']
    can_delete = False


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'workspace', 'is_archived', 'created_at', 'updated_at']
    list_filter = ['workspace', 'is_archived', 'created_at']
    search_fields = ['title', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'role', 'short_content', 'tokens_used', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content']
    readonly_fields = ['created_at']

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    short_content.short_description = 'Contenu'


admin.site.site_header = 'TaskFlow Administration'
admin.site.site_title = 'TaskFlow'
admin.site.index_title = "Bienvenue dans l'administration TaskFlow"
