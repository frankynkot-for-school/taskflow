from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Project, Task, SubTask, Tag, Comment, Attachment


# Personnalisation de l'admin User
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']


class SubTaskInline(admin.TabularInline):
    model = SubTask
    extra = 1


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ['author', 'created_at']


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ['uploaded_by', 'uploaded_at']


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ['title', 'status', 'priority', 'assignee', 'due_date']
    readonly_fields = ['created_at']
    show_change_link = True


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'created_at', 'tasks_count', 'members_count']
    list_filter = ['created_at', 'owner']
    search_fields = ['title', 'description', 'owner__username']
    filter_horizontal = ['members']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [TaskInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'description')
        }),
        ('Propriétaire et membres', {
            'fields': ('owner', 'members')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def tasks_count(self, obj):
        return obj.tasks.count()
    tasks_count.short_description = 'Nombre de tâches'
    
    def members_count(self, obj):
        return obj.members.count()
    members_count.short_description = 'Membres'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'status', 'priority', 'assignee', 'due_date', 'created_at']
    list_filter = ['status', 'priority', 'project', 'created_at', 'due_date']
    search_fields = ['title', 'description', 'project__title', 'assignee__username']
    filter_horizontal = ['tags']
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'created_by']
    list_editable = ['status', 'priority']
    date_hierarchy = 'created_at'
    inlines = [SubTaskInline, CommentInline, AttachmentInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'description', 'project')
        }),
        ('Assignation et statut', {
            'fields': ('assignee', 'status', 'priority', 'tags')
        }),
        ('Dates', {
            'fields': ('due_date', 'created_at', 'updated_at', 'completed_at')
        }),
        ('Créé par', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouvelle tâche
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'task', 'is_completed', 'created_at']
    list_filter = ['is_completed', 'task__project', 'created_at']
    search_fields = ['title', 'task__title']
    list_editable = ['is_completed']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'tasks_count']
    search_fields = ['name']
    
    def tasks_count(self, obj):
        return obj.tasks.count()
    tasks_count.short_description = 'Tâches associées'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'author', 'short_content', 'created_at']
    list_filter = ['created_at', 'author', 'task__project']
    search_fields = ['content', 'author__username', 'task__title']
    readonly_fields = ['created_at', 'updated_at']
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Contenu'


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['task', 'file', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at', 'uploaded_by', 'task__project']
    search_fields = ['task__title', 'uploaded_by__username']
    readonly_fields = ['uploaded_at']


# Personnalisation du site admin
admin.site.site_header = "TaskFlow Administration"
admin.site.site_title = "TaskFlow"
admin.site.index_title = "Bienvenue dans l'administration TaskFlow"
