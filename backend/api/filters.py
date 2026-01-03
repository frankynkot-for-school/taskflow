import django_filters
from django.db.models import Q
from .models import Project, Task


class ProjectFilter(django_filters.FilterSet):
    """Filtres pour les projets"""
    title = django_filters.CharFilter(lookup_expr='icontains')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Project
        fields = ['title', 'created_after', 'created_before']


class TaskFilter(django_filters.FilterSet):
    """Filtres avancés pour les tâches"""
    title = django_filters.CharFilter(lookup_expr='icontains')
    project = django_filters.NumberFilter(field_name='project__id')
    status = django_filters.ChoiceFilter(choices=Task.STATUS_CHOICES)
    priority = django_filters.ChoiceFilter(choices=Task.PRIORITY_CHOICES)
    assignee = django_filters.NumberFilter(field_name='assignee__id')
    assignee_username = django_filters.CharFilter(field_name='assignee__username', lookup_expr='icontains')
    tags = django_filters.CharFilter(method='filter_by_tags')
    due_date_after = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='gte')
    due_date_before = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    is_overdue = django_filters.BooleanFilter(method='filter_overdue')
    has_assignee = django_filters.BooleanFilter(method='filter_has_assignee')
    
    class Meta:
        model = Task
        fields = [
            'title', 'project', 'status', 'priority', 'assignee', 
            'assignee_username', 'tags', 'due_date_after', 'due_date_before',
            'created_after', 'created_before', 'is_overdue', 'has_assignee'
        ]
    
    def filter_by_tags(self, queryset, name, value):
        """Filtre par tags (IDs séparés par des virgules)"""
        tag_ids = [int(id) for id in value.split(',') if id.isdigit()]
        if tag_ids:
            return queryset.filter(tags__id__in=tag_ids).distinct()
        return queryset
    
    def filter_overdue(self, queryset, name, value):
        """Filtre les tâches en retard"""
        from django.utils import timezone
        if value:
            return queryset.filter(
                due_date__lt=timezone.now(),
                status__in=['todo', 'in_progress', 'review']
            )
        return queryset.filter(
            Q(due_date__gte=timezone.now()) | Q(due_date__isnull=True) | Q(status='done')
        )
    
    def filter_has_assignee(self, queryset, name, value):
        """Filtre les tâches avec/sans assigné"""
        if value:
            return queryset.filter(assignee__isnull=False)
        return queryset.filter(assignee__isnull=True)
