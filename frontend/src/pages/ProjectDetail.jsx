import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FiArrowLeft,
  FiPlus,
  FiEdit,
  FiTrash2,
  FiUsers,
  FiCheckSquare,
} from 'react-icons/fi';
import { useProjectStore, useTaskStore, useTagStore } from '../store/dataStore';
import Modal from '../components/Modal';
import TaskCard from '../components/TaskCard';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';

const ProjectDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { currentProject, fetchProject, updateProject, deleteProject, clearCurrentProject } = useProjectStore();
  const { tasks, fetchTasks, createTask } = useTaskStore();
  const { tags, fetchTags } = useTagStore();

  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  const [taskFormData, setTaskFormData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    due_date: '',
    tag_ids: [],
  });
  const [projectFormData, setProjectFormData] = useState({
    title: '',
    description: '',
  });

  useEffect(() => {
    fetchProject(id);
    fetchTasks({ project: id });
    fetchTags();

    return () => clearCurrentProject();
  }, [id, fetchProject, fetchTasks, fetchTags, clearCurrentProject]);

  useEffect(() => {
    if (currentProject) {
      setProjectFormData({
        title: currentProject.title,
        description: currentProject.description || '',
      });
    }
  }, [currentProject]);

  const projectTasks = tasks.filter((task) => task.project === parseInt(id));

  const filteredTasks = activeTab === 'all'
    ? projectTasks
    : projectTasks.filter((task) => task.status === activeTab);

  const handleCreateTask = async (e) => {
    e.preventDefault();
    const result = await createTask({
      ...taskFormData,
      project: parseInt(id),
    });

    if (result.success) {
      toast.success('Tâche créée');
      setIsTaskModalOpen(false);
      setTaskFormData({
        title: '',
        description: '',
        priority: 'medium',
        due_date: '',
        tag_ids: [],
      });
      fetchTasks({ project: id });
    } else {
      toast.error('Erreur lors de la création');
    }
  };

  const handleUpdateProject = async (e) => {
    e.preventDefault();
    const result = await updateProject(id, projectFormData);
    if (result.success) {
      toast.success('Projet mis à jour');
      setIsEditModalOpen(false);
    } else {
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const handleDeleteProject = async () => {
    if (window.confirm('Supprimer ce projet et toutes ses tâches ?')) {
      const result = await deleteProject(id);
      if (result.success) {
        toast.success('Projet supprimé');
        navigate('/projects');
      } else {
        toast.error('Erreur lors de la suppression');
      }
    }
  };

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  const statusTabs = [
    { key: 'all', label: 'Toutes', count: projectTasks.length },
    { key: 'todo', label: 'À faire', count: projectTasks.filter((t) => t.status === 'todo').length },
    { key: 'in_progress', label: 'En cours', count: projectTasks.filter((t) => t.status === 'in_progress').length },
    { key: 'review', label: 'En révision', count: projectTasks.filter((t) => t.status === 'review').length },
    { key: 'done', label: 'Terminé', count: projectTasks.filter((t) => t.status === 'done').length },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/projects')}
            className="p-2 rounded-lg hover:bg-gray-100"
          >
            <FiArrowLeft className="text-gray-500" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{currentProject.title}</h1>
            {currentProject.description && (
              <p className="text-gray-500 mt-1">{currentProject.description}</p>
            )}
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
            onClick={handleDeleteProject}
            className="btn btn-danger flex items-center gap-2"
          >
            <FiTrash2 />
            Supprimer
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FiCheckSquare className="text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-800">{projectTasks.length}</p>
              <p className="text-sm text-gray-500">Tâches totales</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <FiCheckSquare className="text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-800">
                {projectTasks.filter((t) => t.status === 'done').length}
              </p>
              <p className="text-sm text-gray-500">Terminées</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary-100 rounded-lg">
              <FiUsers className="text-primary-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-800">{currentProject.members?.length || 0}</p>
              <p className="text-sm text-gray-500">Membres</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <FiCheckSquare className="text-yellow-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-800">{currentProject.progress}%</p>
              <p className="text-sm text-gray-500">Progression</p>
            </div>
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="card p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="font-medium text-gray-700">Progression du projet</span>
          <span className="text-gray-500">{currentProject.progress}%</span>
        </div>
        <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${currentProject.progress}%` }}
            className="h-full bg-primary-500 rounded-full"
          />
        </div>
      </div>

      {/* Tasks */}
      <div className="card">
        {/* Tabs */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-gray-200">
          <div className="flex gap-1 overflow-x-auto">
            {statusTabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                  activeTab === tab.key
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {tab.label} ({tab.count})
              </button>
            ))}
          </div>
          <button
            onClick={() => setIsTaskModalOpen(true)}
            className="btn btn-primary flex items-center gap-2"
          >
            <FiPlus />
            Nouvelle tâche
          </button>
        </div>

        {/* Task list */}
        <div className="p-6">
          {filteredTasks.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredTasks.map((task) => (
                <Link key={task.id} to={`/tasks/${task.id}`}>
                  <TaskCard task={task} />
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <FiCheckSquare className="mx-auto text-4xl text-gray-300 mb-4" />
              <p className="text-gray-500">Aucune tâche dans cette catégorie</p>
            </div>
          )}
        </div>
      </div>

      {/* Task Modal */}
      <Modal
        isOpen={isTaskModalOpen}
        onClose={() => setIsTaskModalOpen(false)}
        title="Nouvelle tâche"
      >
        <form onSubmit={handleCreateTask} className="space-y-4">
          <div>
            <label className="label">Titre *</label>
            <input
              type="text"
              value={taskFormData.title}
              onChange={(e) => setTaskFormData({ ...taskFormData, title: e.target.value })}
              className="input"
              placeholder="Titre de la tâche"
              required
            />
          </div>
          <div>
            <label className="label">Description</label>
            <textarea
              value={taskFormData.description}
              onChange={(e) => setTaskFormData({ ...taskFormData, description: e.target.value })}
              className="input"
              rows={3}
              placeholder="Description..."
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Priorité</label>
              <select
                value={taskFormData.priority}
                onChange={(e) => setTaskFormData({ ...taskFormData, priority: e.target.value })}
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
                value={taskFormData.due_date}
                onChange={(e) => setTaskFormData({ ...taskFormData, due_date: e.target.value })}
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
                  className={`px-3 py-1 rounded-full text-sm cursor-pointer transition-colors ${
                    taskFormData.tag_ids.includes(tag.id)
                      ? 'ring-2 ring-primary-500'
                      : ''
                  }`}
                  style={{ backgroundColor: tag.color + '20', color: tag.color }}
                >
                  <input
                    type="checkbox"
                    className="hidden"
                    checked={taskFormData.tag_ids.includes(tag.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setTaskFormData({
                          ...taskFormData,
                          tag_ids: [...taskFormData.tag_ids, tag.id],
                        });
                      } else {
                        setTaskFormData({
                          ...taskFormData,
                          tag_ids: taskFormData.tag_ids.filter((id) => id !== tag.id),
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
            <button type="button" onClick={() => setIsTaskModalOpen(false)} className="btn btn-secondary">
              Annuler
            </button>
            <button type="submit" className="btn btn-primary">
              Créer
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Project Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Modifier le projet"
      >
        <form onSubmit={handleUpdateProject} className="space-y-4">
          <div>
            <label className="label">Titre *</label>
            <input
              type="text"
              value={projectFormData.title}
              onChange={(e) => setProjectFormData({ ...projectFormData, title: e.target.value })}
              className="input"
              required
            />
          </div>
          <div>
            <label className="label">Description</label>
            <textarea
              value={projectFormData.description}
              onChange={(e) => setProjectFormData({ ...projectFormData, description: e.target.value })}
              className="input"
              rows={4}
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={() => setIsEditModalOpen(false)} className="btn btn-secondary">
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

export default ProjectDetail;
