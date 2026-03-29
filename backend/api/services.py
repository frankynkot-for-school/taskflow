"""Services metier pour l'application TaskFlow."""

import logging
from decouple import config

from .models import ActivityLog, ActivityType

logger = logging.getLogger(__name__)


class ActivityService:
    """Service pour enregistrer les activites dans le journal."""

    @staticmethod
    def log_task_created(task, user):
        """Log la creation d'une tache."""
        return ActivityLog.objects.create(
            workspace=task.workspace,
            task=task,
            user=user,
            activity_type=ActivityType.TASK_CREATED,
            task_title=task.title,
            new_value={
                'title': task.title,
                'status': task.status,
                'priority': task.priority,
            },
        )

    @staticmethod
    def log_task_updated(task, user, changes):
        """Log la modification d'une tache."""
        return ActivityLog.objects.create(
            workspace=task.workspace,
            task=task,
            user=user,
            activity_type=ActivityType.TASK_UPDATED,
            task_title=task.title,
            old_value=changes.get('old'),
            new_value=changes.get('new'),
        )

    @staticmethod
    def log_status_change(task, user, old_status, new_status):
        """Log un changement de statut."""
        return ActivityLog.objects.create(
            workspace=task.workspace,
            task=task,
            user=user,
            activity_type=ActivityType.TASK_STATUS_CHANGED,
            task_title=task.title,
            old_value={'status': old_status},
            new_value={'status': new_status},
        )

    @staticmethod
    def log_assignment(task, user, old_assignee, new_assignee):
        """Log une assignation ou desassignation."""
        activity_type = ActivityType.TASK_ASSIGNED if new_assignee else ActivityType.TASK_UNASSIGNED
        return ActivityLog.objects.create(
            workspace=task.workspace,
            task=task,
            user=user,
            activity_type=activity_type,
            task_title=task.title,
            old_value={
                'assignee_id': old_assignee.id if old_assignee else None,
                'assignee_name': old_assignee.username if old_assignee else None,
            },
            new_value={
                'assignee_id': new_assignee.id if new_assignee else None,
                'assignee_name': new_assignee.username if new_assignee else None,
            },
            target_user=new_assignee,
        )

    @staticmethod
    def log_subtask_added(parent_task, subtask, user):
        """Log l'ajout d'une sous-tache."""
        return ActivityLog.objects.create(
            workspace=parent_task.workspace,
            task=parent_task,
            user=user,
            activity_type=ActivityType.SUBTASK_ADDED,
            task_title=parent_task.title,
            new_value={
                'subtask_id': subtask.id,
                'subtask_title': subtask.title,
            },
        )

    @staticmethod
    def log_subtask_removed(parent_task, subtask_title, user):
        """Log la suppression d'une sous-tache."""
        return ActivityLog.objects.create(
            workspace=parent_task.workspace,
            task=parent_task,
            user=user,
            activity_type=ActivityType.SUBTASK_REMOVED,
            task_title=parent_task.title,
            old_value={'subtask_title': subtask_title},
        )

    @staticmethod
    def log_comment_added(comment, user):
        """Log l'ajout d'un commentaire."""
        return ActivityLog.objects.create(
            workspace=comment.task.workspace,
            task=comment.task,
            user=user,
            activity_type=ActivityType.COMMENT_ADDED,
            task_title=comment.task.title,
            new_value={
                'comment_id': comment.id,
                'preview': comment.content[:100],
            },
        )

    @staticmethod
    def log_comment_deleted(task, comment_preview, user):
        """Log la suppression d'un commentaire."""
        return ActivityLog.objects.create(
            workspace=task.workspace,
            task=task,
            user=user,
            activity_type=ActivityType.COMMENT_DELETED,
            task_title=task.title,
            old_value={'preview': comment_preview},
        )


class MistralService:
    """Service pour interagir avec l'API Mistral."""

    MODEL = "mistral-large-latest"
    MAX_CONTEXT_TASKS = 10
    MAX_HISTORY_MESSAGES = 20

    def __init__(self):
        api_key = config('MISTRAL_API_KEY', default='')
        if not api_key:
            raise ValueError("MISTRAL_API_KEY n'est pas configurée. Veuillez définer la variable d'environnement MISTRAL_API_KEY.")
        try:
            from mistralai.client import Mistral
            self.client = Mistral(api_key=api_key)
        except ImportError:
            raise ValueError("Le paquet 'mistralai' n'est pas installé. Installez-le avec: pip install mistralai")

    @staticmethod
    def build_system_prompt(user, workspace, tasks):
        """Construit le prompt systeme avec contexte taches."""
        task_summary = MistralService._format_tasks_for_context(tasks)
        role = workspace.get_user_role(user) or 'member'

        return f"""Tu es un assistant intelligent pour TaskFlow, une application de gestion de taches.

## Contexte Utilisateur
- Nom: {user.first_name or user.username}
- Workspace actuel: {workspace.name}
- Role: {role}

## Taches de l'Utilisateur (les plus recentes)
{task_summary}

## Tes Capacites
- Aider a organiser et prioriser les taches
- Suggerer des sous-taches pour des projets complexes
- Donner des conseils de productivite
- Repondre aux questions sur les taches existantes
- Aider a rediger des descriptions de taches

## Regles
- Reponds toujours en francais
- Sois concis et utile
- Ne partage jamais d'informations sensibles
- Si une tache n'existe pas, dis-le clairement
- Pour creer/modifier des taches, guide l'utilisateur vers l'interface

Reponds de maniere naturelle et aide l'utilisateur a etre plus productif.
"""

    @staticmethod
    def _format_tasks_for_context(tasks):
        """Formate les taches pour le contexte LLM."""
        if not tasks:
            return "Aucune tache actuellement."

        status_map = {
            'todo': 'A faire',
            'in_progress': 'En cours',
            'review': 'En revision',
            'done': 'Termine'
        }
        priority_map = {
            'low': 'Basse',
            'medium': 'Moyenne',
            'high': 'Haute',
            'urgent': 'Urgente'
        }

        lines = []
        for task in tasks[:MistralService.MAX_CONTEXT_TASKS]:
            due_info = ""
            if task.due_date:
                due_info = f", Echeance: {task.due_date.strftime('%d/%m/%Y')}"

            assignee_info = ""
            if task.assignee:
                assignee_info = f", Assigne a: {task.assignee.username}"

            lines.append(
                f"- [{task.id}] {task.title} | "
                f"Statut: {status_map.get(task.status, task.status)} | "
                f"Priorite: {priority_map.get(task.priority, task.priority)}"
                f"{due_info}{assignee_info}"
            )

        if len(tasks) > MistralService.MAX_CONTEXT_TASKS:
            lines.append(f"... et {len(tasks) - MistralService.MAX_CONTEXT_TASKS} autres taches")

        return "\n".join(lines)

    @staticmethod
    def get_relevant_tasks(user, workspace):
        """Recupere les taches pertinentes pour le contexte."""
        from .models import Task
        from django.db.models import Q

        tasks = Task.objects.filter(
            workspace=workspace
        ).filter(
            Q(assignee=user) | Q(created_by=user)
        ).exclude(
            status='done'
        ).select_related(
            'assignee'
        ).order_by(
            'due_date',
            '-priority',
            '-created_at'
        )[:MistralService.MAX_CONTEXT_TASKS]

        return list(tasks)

    def chat(self, conversation, user_message):
        """Envoie un message et recupere la reponse de Mistral."""
        from .models import ChatMessage, ChatMessageRole

        workspace = conversation.workspace
        user = conversation.user

        # Recuperer les taches pertinentes
        tasks = self.get_relevant_tasks(user, workspace)

        # Construire le prompt systeme
        system_prompt = self.build_system_prompt(user, workspace, tasks)

        # Construire les messages pour Mistral
        messages = [{"role": "system", "content": system_prompt}]

        # Ajouter l'historique de conversation
        history = conversation.messages.order_by('-created_at')[:self.MAX_HISTORY_MESSAGES]
        for msg in reversed(list(history)):
            if msg.role != 'system':
                messages.append({"role": msg.role, "content": msg.content})

        # Ajouter le message utilisateur
        messages.append({"role": "user", "content": user_message})

        # Sauvegarder le contexte des taches
        task_context = {
            'task_ids': [t.id for t in tasks],
            'task_count': len(tasks),
        }

        # Sauvegarder le message utilisateur
        ChatMessage.objects.create(
            conversation=conversation,
            role=ChatMessageRole.USER,
            content=user_message,
            task_context=task_context,
        )

        try:
            # Appeler l'API Mistral
            response = self.client.chat.complete(
                model=self.MODEL,
                messages=messages,
            )

            assistant_content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None

            # Sauvegarder la reponse de l'assistant
            assistant_msg = ChatMessage.objects.create(
                conversation=conversation,
                role=ChatMessageRole.ASSISTANT,
                content=assistant_content,
                tokens_used=tokens_used,
            )

            # Generer un titre si premiere conversation
            if conversation.messages.count() <= 2:
                conversation.generate_title()

            # Mettre a jour le timestamp
            conversation.save(update_fields=['updated_at'])

            return {
                'success': True,
                'message': assistant_msg,
                'tokens_used': tokens_used,
            }

        except Exception as e:
            logger.error(f"Erreur API Mistral: {str(e)}")
            return {
                'success': False,
                'error': "Erreur lors de la communication avec l'assistant. Veuillez reessayer.",
            }

