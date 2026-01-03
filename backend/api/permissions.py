from rest_framework import permissions


class IsProjectOwner(permissions.BasePermission):
    """
    Permission qui autorise uniquement le propriétaire du projet à le modifier/supprimer.
    """
    
    def has_object_permission(self, request, view, obj):
        # Les permissions de lecture sont autorisées pour les membres
        if request.method in permissions.SAFE_METHODS:
            return obj.owner == request.user or request.user in obj.members.all()
        
        # Les permissions d'écriture ne sont autorisées qu'au propriétaire
        return obj.owner == request.user


class IsProjectMember(permissions.BasePermission):
    """
    Permission qui vérifie si l'utilisateur est membre du projet.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user in obj.members.all()


class IsTaskProjectMember(permissions.BasePermission):
    """
    Permission qui vérifie si l'utilisateur est membre du projet de la tâche.
    """
    
    def has_object_permission(self, request, view, obj):
        project = obj.project
        return project.owner == request.user or request.user in project.members.all()


class IsCommentAuthorOrReadOnly(permissions.BasePermission):
    """
    Permission qui autorise uniquement l'auteur du commentaire à le modifier/supprimer.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsAttachmentUploaderOrProjectMember(permissions.BasePermission):
    """
    Permission pour les pièces jointes.
    """
    
    def has_object_permission(self, request, view, obj):
        project = obj.task.project
        # Lecture autorisée pour les membres du projet
        if request.method in permissions.SAFE_METHODS:
            return project.owner == request.user or request.user in project.members.all()
        # Suppression autorisée uniquement pour celui qui a uploadé
        return obj.uploaded_by == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission générique - lecture pour tous, écriture pour le propriétaire.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Vérifier différents attributs de propriété
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        if hasattr(obj, 'author'):
            return obj.author == request.user
        if hasattr(obj, 'uploaded_by'):
            return obj.uploaded_by == request.user
        
        return False
