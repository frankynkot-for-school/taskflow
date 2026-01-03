import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FiArrowLeft,
  FiEdit,
  FiTrash2,
  FiCalendar,
  FiUser,
  FiTag,
  FiMessageSquare,
  FiPaperclip,
  FiPlus,
  FiCheck,
  FiX,
  FiSend,
} from 'react-icons/fi';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { useTaskStore, useTagStore } from '../store/dataStore';
import { subtaskService, commentService } from '../services/api';
import Modal from '../components/Modal';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';

const TaskDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { currentTask, fetchTask, updateTask, deleteTask, changeTaskStatus, clearCurrentTask } = useTaskStore();
  const { tags, fetchTags } = useTagStore();

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [newSubtask, setNewSubtask] = useState('');
  const [newComment, setNewComment] = useState('');
  const [subtasks, setSubtasks] = useState([]);
  const [comments, setComments] = useState([]);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    due_date: '',
    tag_ids: [],
  });

  useEffect(() => {
    fetchTask(id);
    fetchTags();

    return () => clearCurrentTask();
  }, [id, fetchTask, fetchTags, clearCurrentTask]);

  useEffect(() => {
    if (currentTask) {
      setFormData({
        title: currentTask.title,
        description: currentTask.description || '',
        priority: currentTask.priority,
        due_date: currentTask.due_date ? currentTask.due_date.slice(0, 16) : '',
        tag_ids: currentTask.tags?.map((t) => t.id) || [],
      });
      setSubtasks(currentTask.subtasks || []);
      setComments(currentTask.comments || []);
    }
  }, [currentTask]);

  const handleUpdateTask = async (e) => {
    e.preventDefault();
    const result = await updateTask(id, formData);
    if (result.success) {
      toast.success('Tâche mise à jour');
      setIsEditModalOpen(false);
      fetchTask(id);
    } else {
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const handleDeleteTask = async () => {
    if (window.confirm('Supprimer cette tâche ?')) {
      const result = await deleteTask(id);
      if (result.success) {
        toast.success('Tâche supprimée');
        navigate(-1);
      } else {
        toast.error('Erreur lors de la suppression');
      }
    }
  };

  const handleStatusChange = async (newStatus) => {
    const result = await changeTaskStatus(id, newStatus);
    if (result.success) {
      toast.success('Statut mis à jour');
      fetchTask(id);
    } else {
      toast.error('Erreur lors du changement de statut');
    }
  };

  const handleAddSubtask = async (e) => {
    e.preventDefault();
    if (!newSubtask.trim()) return;

    try {
      const subtask = await subtaskService.create({
        task: parseInt(id),
        title: newSubtask,
      });
      setSubtasks([...subtasks, subtask]);
      setNewSubtask('');
      toast.success('Sous-tâche ajoutée');
    } catch (error) {
      toast.error('Erreur');
    }
  };

  const handleToggleSubtask = async (subtaskId) => {
    try {
      const updated = await subtaskService.toggleComplete(subtaskId);
      setSubtasks(subtasks.map((s) => (s.id === subtaskId ? updated : s)));
    } catch (error) {
      toast.error('Erreur');
    }
  };

  const handleDeleteSubtask = async (subtaskId) => {
    try {
      await subtaskService.delete(subtaskId);
      setSubtasks(subtasks.filter((s) => s.id !== subtaskId));
      toast.success('Sous-tâche supprimée');
    } catch (error) {
      toast.error('Erreur');
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    try {
      const comment = await commentService.create({
        task: parseInt(id),
        content: newComment,
      });
      setComments([comment, ...comments]);
      setNewComment('');
      toast.success('Commentaire ajouté');
    } catch (error) {
      toast.error('Erreur');
    }
  };

  if (!currentTask) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const statusOptions = [
    { value: 'todo', label: 'À faire', color: 'bg-gray-100 text-gray-800' },
    { value: 'in_progress', label: 'En cours', color: 'bg-blue-100 text-blue-800' },
    { value: 'review', label: 'En révision', color: 'bg-yellow-100 text-yellow-800' },
    { value: 'done', label: 'Terminé', color: 'bg-green-100 text-green-800' },
  ];

  const priorityStyles = {
    low: 'bg-gray-100 text-gray-600',
    medium: 'bg-blue-100 text-blue-600',
    high: 'bg-orange-100 text-orange-600',
    urgent: 'bg-red-100 text-red-600',
  };

  const priorityLabels = {
    low: 'Basse',
    medium: 'Moyenne',
    high: 'Haute',
    urgent: 'Urgente',
  };

  const completedSubtasks = subtasks.filter((s) => s.is_completed).length;
  const progress = subtasks.length > 0 ? Math.round((completedSubtasks / subtasks.length) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 rounded-lg hover:bg-gray-100"
          >
            <FiArrowLeft className="text-gray-500" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{currentTask.title}</h1>
            <div className="flex items-center gap-3 mt-2">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityStyles[currentTask.priority]}`}>
                {priorityLabels[currentTask.priority]}
              </span>
              {currentTask.due_date && (
                <span className="flex items-center gap-1 text-sm text-gray-500">
                  <FiCalendar />
                  {format(new Date(currentTask.due_date), "d MMM yyyy 'à' HH:mm", { locale: fr })}
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsEditModalOpen(true)}
            className="btn btn-secondary flex items-center gap-2"
          >
            <FiEdit />
            Modifier
          </button>
          <button
            onClick={handleDeleteTask}
            className="btn btn-danger flex items-center gap-2"
          >
            <FiTrash2 />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Status */}
          <div className="card p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-3">Statut</h3>
            <div className="flex flex-wrap gap-2">
              {statusOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleStatusChange(option.value)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    currentTask.status === option.value
                      ? `${option.color} ring-2 ring-offset-2 ring-primary-500`
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Description */}
          <div className="card p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-3">Description</h3>
            <p className="text-gray-700 whitespace-pre-wrap">
              {currentTask.description || 'Aucune description'}
            </p>
          </div>

          {/* Subtasks */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-500">
                Sous-tâches ({completedSubtasks}/{subtasks.length})
              </h3>
              {subtasks.length > 0 && (
                <span className="text-sm text-gray-500">{progress}%</span>
              )}
            </div>

            {/* Progress bar */}
            {subtasks.length > 0 && (
              <div className="w-full h-2 bg-gray-200 rounded-full mb-4 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  className="h-full bg-green-500 rounded-full"
                />
              </div>
            )}

            {/* Subtask list */}
            <div className="space-y-2 mb-4">
              {subtasks.map((subtask) => (
                <div
                  key={subtask.id}
                  className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 group"
                >
                  <button
                    onClick={() => handleToggleSubtask(subtask.id)}
                    className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                      subtask.is_completed
                        ? 'bg-green-500 border-green-500 text-white'
                        : 'border-gray-300 hover:border-green-500'
                    }`}
                  >
                    {subtask.is_completed && <FiCheck className="text-xs" />}
                  </button>
                  <span
                    className={`flex-1 ${
                      subtask.is_completed ? 'line-through text-gray-400' : 'text-gray-700'
                    }`}
                  >
                    {subtask.title}
                  </span>
                  <button
                    onClick={() => handleDeleteSubtask(subtask.id)}
                    className="p-1 rounded hover:bg-gray-200 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <FiX className="text-gray-400" />
                  </button>
                </div>
              ))}
            </div>

            {/* Add subtask form */}
            <form onSubmit={handleAddSubtask} className="flex gap-2">
              <input
                type="text"
                value={newSubtask}
                onChange={(e) => setNewSubtask(e.target.value)}
                placeholder="Ajouter une sous-tâche..."
                className="input flex-1"
              />
              <button type="submit" className="btn btn-primary">
                <FiPlus />
              </button>
            </form>
          </div>

          {/* Comments */}
          <div className="card p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-4 flex items-center gap-2">
              <FiMessageSquare />
              Commentaires ({comments.length})
            </h3>

            {/* Add comment form */}
            <form onSubmit={handleAddComment} className="flex gap-2 mb-4">
              <input
                type="text"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Ajouter un commentaire..."
                className="input flex-1"
              />
              <button type="submit" className="btn btn-primary">
                <FiSend />
              </button>
            </form>

            {/* Comments list */}
            <div className="space-y-4">
              {comments.map((comment) => (
                <div key={comment.id} className="flex gap-3">
                  <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-medium text-primary-600">
                      {comment.author?.username?.charAt(0).toUpperCase() || 'U'}
                    </span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-gray-800">
                        {comment.author?.username || 'Utilisateur'}
                      </span>
                      <span className="text-xs text-gray-400">
                        {format(new Date(comment.created_at), "d MMM 'à' HH:mm", { locale: fr })}
                      </span>
                    </div>
                    <p className="text-gray-600">{comment.content}</p>
                  </div>
                </div>
              ))}
              {comments.length === 0 && (
                <p className="text-center text-gray-400 py-4">Aucun commentaire</p>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Project info */}
          <div className="card p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-3">Projet</h3>
            <Link
              to={`/projects/${currentTask.project}`}
              className="text-primary-600 hover:underline font-medium"
            >
              Voir le projet →
            </Link>
          </div>

          {/* Assignee */}
          <div className="card p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-3 flex items-center gap-2">
              <FiUser />
              Assigné à
            </h3>
            {currentTask.assignee ? (
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="font-medium text-primary-600">
                    {currentTask.assignee.username.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="font-medium text-gray-800">{currentTask.assignee.username}</p>
                  <p className="text-sm text-gray-500">{currentTask.assignee.email}</p>
                </div>
              </div>
            ) : (
              <p className="text-gray-400">Non assigné</p>
            )}
          </div>

          {/* Tags */}
          <div className="card p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-3 flex items-center gap-2">
              <FiTag />
              Tags
            </h3>
            {currentTask.tags && currentTask.tags.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {currentTask.tags.map((tag) => (
                  <span
                    key={tag.id}
                    className="px-3 py-1 rounded-full text-sm font-medium"
                    style={{ backgroundColor: tag.color + '20', color: tag.color }}
                  >
                    {tag.name}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-gray-400">Aucun tag</p>
            )}
          </div>

          {/* Attachments */}
          <div className="card p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-3 flex items-center gap-2">
              <FiPaperclip />
              Pièces jointes
            </h3>
            {currentTask.attachments && currentTask.attachments.length > 0 ? (
              <div className="space-y-2">
                {currentTask.attachments.map((attachment) => (
                  <a
                    key={attachment.id}
                    href={attachment.file}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 p-2 rounded hover:bg-gray-50"
                  >
                    <FiPaperclip className="text-gray-400" />
                    <span className="text-sm text-primary-600 hover:underline truncate">
                      {attachment.file_name}
                    </span>
                  </a>
                ))}
              </div>
            ) : (
              <p className="text-gray-400">Aucune pièce jointe</p>
            )}
          </div>

          {/* Dates */}
          <div className="card p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-3">Dates</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Créé le</span>
                <span className="text-gray-700">
                  {format(new Date(currentTask.created_at), 'd MMM yyyy', { locale: fr })}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Modifié le</span>
                <span className="text-gray-700">
                  {format(new Date(currentTask.updated_at), 'd MMM yyyy', { locale: fr })}
                </span>
              </div>
              {currentTask.completed_at && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Terminé le</span>
                  <span className="text-green-600">
                    {format(new Date(currentTask.completed_at), 'd MMM yyyy', { locale: fr })}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Edit Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Modifier la tâche"
        size="lg"
      >
        <form onSubmit={handleUpdateTask} className="space-y-4">
          <div>
            <label className="label">Titre *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="input"
              required
            />
          </div>
          <div>
            <label className="label">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="input"
              rows={4}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Priorité</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="input"
              >
                <option value="low">Basse</option>
                <option value="medium">Moyenne</option>
                <option value="high">Haute</option>
                <option value="urgent">Urgente</option>
              </select>
            </div>
            <div>
              <label className="label">Échéance</label>
              <input
                type="datetime-local"
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                className="input"
              />
            </div>
          </div>
          <div>
            <label className="label">Tags</label>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => (
                <label
                  key={tag.id}
                  className={`px-3 py-1 rounded-full text-sm cursor-pointer transition-all ${
                    formData.tag_ids.includes(tag.id)
                      ? 'ring-2 ring-primary-500'
                      : ''
                  }`}
                  style={{ backgroundColor: tag.color + '20', color: tag.color }}
                >
                  <input
                    type="checkbox"
                    className="hidden"
                    checked={formData.tag_ids.includes(tag.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setFormData({
                          ...formData,
                          tag_ids: [...formData.tag_ids, tag.id],
                        });
                      } else {
                        setFormData({
                          ...formData,
                          tag_ids: formData.tag_ids.filter((tid) => tid !== tag.id),
                        });
                      }
                    }}
                  />
                  {tag.name}
                </label>
              ))}
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => setIsEditModalOpen(false)}
              className="btn btn-secondary"
            >
              Annuler
            </button>
            <button type="submit" className="btn btn-primary">
              Mettre à jour
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default TaskDetail;
