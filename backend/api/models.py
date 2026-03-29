from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class HierarchyRole(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    MANAGER = 'manager', 'Manager'
    TEAM_LEAD = 'team_lead', 'Team Lead'
    MEMBER = 'member', 'Member'


class WorkspaceType(models.TextChoices):
    """Types de workspace."""
    PERSONAL = 'personal', 'Personnel'
    TEAM = 'team', 'Équipe'
    ORGANIZATION = 'organization', 'Organisation'


class Workspace(models.Model):
    """Espace de travail contenant membres et taches (style Notion)."""

    # Couleurs prédéfinies pour les workspaces
    COLOR_CHOICES = [
        ('#6366F1', 'Indigo'),
        ('#8B5CF6', 'Violet'),
        ('#EC4899', 'Rose'),
        ('#EF4444', 'Rouge'),
        ('#F97316', 'Orange'),
        ('#EAB308', 'Jaune'),
        ('#22C55E', 'Vert'),
        ('#14B8A6', 'Teal'),
        ('#3B82F6', 'Bleu'),
        ('#6B7280', 'Gris'),
    ]

    # Emojis populaires pour les icônes
    ICON_CHOICES = [
        ('🏠', 'Maison'),
        ('💼', 'Travail'),
        ('🚀', 'Fusée'),
        ('⭐', 'Étoile'),
        ('📁', 'Dossier'),
        ('📊', 'Graphique'),
        ('🎯', 'Cible'),
        ('💡', 'Idée'),
        ('🔧', 'Outil'),
        ('📝', 'Note'),
        ('🎨', 'Art'),
        ('🌟', 'Brillant'),
        ('🔥', 'Feu'),
        ('💎', 'Diamant'),
        ('🏆', 'Trophée'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    icon = models.CharField(max_length=10, default='💼')
    color = models.CharField(max_length=7, default='#6366F1', choices=COLOR_CHOICES)
    workspace_type = models.CharField(
        max_length=20,
        choices=WorkspaceType.choices,
        default=WorkspaceType.TEAM,
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_workspaces',
    )
    is_default = models.BooleanField(default=False, help_text="Workspace par défaut de l'utilisateur")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Workspace'
        verbose_name_plural = 'Workspaces'

    def __str__(self):
        return f"{self.icon} {self.name}"

    @classmethod
    def get_default_workspace(cls):
        """Retourne le workspace global (backward compatibility)."""
        workspace, _ = cls.objects.get_or_create(
            name='Workspace Global',
            defaults={
                'description': 'Workspace global unique de TaskFlow',
                'icon': '🌐',
                'color': '#3B82F6',
                'workspace_type': WorkspaceType.ORGANIZATION,
            },
        )
        return workspace

    @classmethod
    def create_personal_workspace(cls, user):
        """Crée un workspace personnel pour un nouvel utilisateur."""
        from api.models import WorkspaceMember, HierarchyRole

        workspace = cls.objects.create(
            name=f"Espace de {user.username}",
            description=f"Espace personnel de {user.username}",
            owner=user,
            icon='🏠',
            color='#6366F1',
            workspace_type=WorkspaceType.PERSONAL,
            is_default=True,
        )
        WorkspaceMember.objects.create(
            user=user,
            workspace=workspace,
            role=HierarchyRole.ADMIN,
        )
        return workspace

    def get_member_count(self):
        """Retourne le nombre de membres."""
        return self.memberships.count()

    def is_member(self, user):
        """Vérifie si l'utilisateur est membre."""
        return self.memberships.filter(user=user).exists()

    def get_user_role(self, user):
        """Retourne le rôle de l'utilisateur dans ce workspace."""
        membership = self.memberships.filter(user=user).first()
        return membership.role if membership else None


class UserProfile(models.Model):
    """Profil utilisateur (le role est gere dans WorkspaceMember)."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.FileField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Profil utilisateur'
        verbose_name_plural = 'Profils utilisateurs'

    def __str__(self):
        return f'Profil de {self.user.username}'


class WorkspaceMember(models.Model):
    """Association User <-> Workspace avec role hierarchique."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspace_memberships')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(
        max_length=20,
        choices=HierarchyRole.choices,
        default=HierarchyRole.MEMBER,
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Membre de workspace'
        verbose_name_plural = 'Membres de workspace'
        constraints = [
            models.UniqueConstraint(fields=['user', 'workspace'], name='uniq_user_workspace'),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.workspace.name} ({self.role})'


class InvitationStatus(models.TextChoices):
    """Statuts d'invitation."""
    PENDING = 'pending', 'En attente'
    ACCEPTED = 'accepted', 'Acceptée'
    DECLINED = 'declined', 'Refusée'
    EXPIRED = 'expired', 'Expirée'


class WorkspaceInvitation(models.Model):
    """Invitation à rejoindre un workspace (style Notion)."""

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='invitations',
    )
    email = models.EmailField(help_text="Email de la personne invitée")
    invited_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='workspace_invitations',
        help_text="Utilisateur invité (si compte existant)",
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
    )
    role = models.CharField(
        max_length=20,
        choices=HierarchyRole.choices,
        default=HierarchyRole.MEMBER,
        help_text="Rôle assigné à l'acceptation",
    )
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
    )
    token = models.CharField(max_length=64, unique=True, help_text="Token unique pour le lien d'invitation")
    message = models.TextField(blank=True, help_text="Message personnalisé")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text="Date d'expiration de l'invitation")
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Invitation workspace'
        verbose_name_plural = 'Invitations workspace'
        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'email'],
                condition=models.Q(status='pending'),
                name='uniq_pending_invitation',
            ),
        ]

    def __str__(self):
        return f"Invitation pour {self.email} à {self.workspace.name}"

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return self.status == InvitationStatus.PENDING and not self.is_expired

    def accept(self, user):
        """Accepte l'invitation et ajoute l'utilisateur au workspace."""
        from django.utils import timezone

        if not self.is_valid:
            raise ValidationError("Cette invitation n'est plus valide.")

        # Créer l'adhésion
        membership, created = WorkspaceMember.objects.get_or_create(
            user=user,
            workspace=self.workspace,
            defaults={'role': self.role},
        )

        if not created:
            # L'utilisateur est déjà membre
            raise ValidationError("Vous êtes déjà membre de ce workspace.")

        self.status = InvitationStatus.ACCEPTED
        self.invited_user = user
        self.accepted_at = timezone.now()
        self.save()

        return membership

    def decline(self):
        """Refuse l'invitation."""
        self.status = InvitationStatus.DECLINED
        self.save()

    @classmethod
    def generate_token(cls):
        """Génère un token unique."""
        import secrets
        return secrets.token_urlsafe(48)


class Tag(models.Model):
    """Etiquettes pour categoriser les taches."""

    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#3B82F6')
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='tags',
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'workspace'],
                name='uniq_tag_name_workspace'
            ),
        ]

    def __str__(self):
        return self.name


class Task(models.Model):
    """Tache hierarchique (parent/enfants) rattachee a un workspace."""

    PRIORITY_CHOICES = [
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('urgent', 'Urgente'),
    ]

    STATUS_CHOICES = [
        ('todo', 'A faire'),
        ('in_progress', 'En cours'),
        ('review', 'En revision'),
        ('done', 'Termine'),
    ]

    title = models.CharField(max_length=200, verbose_name='Titre')
    description = models.TextField(blank=True, verbose_name='Description')
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Workspace',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Tache parente',
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
    )
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    tags = models.ManyToManyField(Tag, related_name='tasks', blank=True)
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='Date echeance')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Tache'
        verbose_name_plural = 'Taches'

    def __str__(self):
        return self.title

    @property
    def is_root(self):
        return self.parent is None

    @property
    def depth(self):
        level = 0
        current = self
        while current.parent is not None:
            level += 1
            current = current.parent
        return level

    def clean(self):
        if self.parent and self.parent.depth >= 2:
            raise ValidationError('La profondeur maximale autorisee est de 2 niveaux.')

    def get_all_children(self):
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_all_children())
        return descendants


class Comment(models.Model):
    """Commentaire sur une tache."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'

    def __str__(self):
        return f'Comment by {self.author.username} on {self.task.title}'


class Attachment(models.Model):
    """Piece jointe pour une tache."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Piece jointe'
        verbose_name_plural = 'Pieces jointes'

    def __str__(self):
        return f'Attachment for {self.task.title}'


class ActivityType(models.TextChoices):
    """Types d'activites tracees dans le journal."""
    TASK_CREATED = 'task_created', 'Tache creee'
    TASK_UPDATED = 'task_updated', 'Tache modifiee'
    TASK_DELETED = 'task_deleted', 'Tache supprimee'
    TASK_STATUS_CHANGED = 'task_status_changed', 'Statut modifie'
    TASK_ASSIGNED = 'task_assigned', 'Tache assignee'
    TASK_UNASSIGNED = 'task_unassigned', 'Tache desassignee'
    SUBTASK_ADDED = 'subtask_added', 'Sous-tache ajoutee'
    SUBTASK_REMOVED = 'subtask_removed', 'Sous-tache retiree'
    COMMENT_ADDED = 'comment_added', 'Commentaire ajoute'
    COMMENT_DELETED = 'comment_deleted', 'Commentaire supprime'


class ActivityLog(models.Model):
    """Journal d'activite pour tracer toutes les actions."""

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='activities',
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activities',
    )
    activity_type = models.CharField(
        max_length=30,
        choices=ActivityType.choices,
    )
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    task_title = models.CharField(max_length=200, blank=True)
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='targeted_activities',
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activite'
        verbose_name_plural = 'Activites'
        indexes = [
            models.Index(fields=['workspace', '-created_at']),
            models.Index(fields=['task', '-created_at']),
        ]

    def __str__(self):
        return f'{self.user} - {self.get_activity_type_display()} - {self.created_at}'


class ChatMessageRole(models.TextChoices):
    """Roles pour les messages de chat."""
    SYSTEM = 'system', 'System'
    USER = 'user', 'User'
    ASSISTANT = 'assistant', 'Assistant'


class ChatConversation(models.Model):
    """Conversation de chat avec l'assistant IA."""

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name='chat_conversations',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_conversations',
    )
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        indexes = [
            models.Index(fields=['workspace', 'user', '-updated_at']),
        ]

    def __str__(self):
        return f'Chat: {self.title or self.id} - {self.user.username}'

    def generate_title(self):
        """Generate title from first user message."""
        first_msg = self.messages.filter(role=ChatMessageRole.USER).first()
        if first_msg:
            self.title = first_msg.content[:50] + ('...' if len(first_msg.content) > 50 else '')
            self.save(update_fields=['title'])


class ChatMessage(models.Model):
    """Message individuel dans une conversation."""

    conversation = models.ForeignKey(
        ChatConversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    role = models.CharField(
        max_length=20,
        choices=ChatMessageRole.choices,
    )
    content = models.TextField()
    task_context = models.JSONField(null=True, blank=True)
    tokens_used = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        return f'{self.role}: {self.content[:50]}...'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Cree automatiquement profil + workspace personnel."""
    if created:
        UserProfile.objects.create(user=instance)
        # Créer un workspace personnel pour le nouvel utilisateur
        Workspace.create_personal_workspace(instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Sauvegarde le profil quand l'utilisateur est sauvegarde."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
