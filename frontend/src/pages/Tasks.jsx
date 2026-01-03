import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FiPlus,
  FiSearch,
  FiFilter,
  FiCheckSquare,
  FiX,
} from 'react-icons/fi';
import { useTaskStore, useProjectStore, useTagStore } from '../store/dataStore';
import Modal from '../components/Modal';
import TaskCard from '../components/TaskCard';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';

const Tasks = () => {
  const { tasks, isLoading, fetchTasks, createTask, filters, setFilters, resetFilters } = useTaskStore();
  const { projects, fetchProjects } = useProjectStore();
  const { tags, fetchTags } = useTagStore();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    project: '',
    priority: 'medium',
    due_date: '',
    tag_ids: [],
  });

  useEffect(() => {
    fetchTasks();
    fetchProjects();
    fetchTags();
  }, [fetchTasks, fetchProjects, fetchTags]);

  useEffect(() => {
    const debounce = setTimeout(() => {
      setFilters({ search: searchTerm });
      fetchTasks();
    }, 300);

    return () => clearTimeout(debounce);
  }, [searchTerm, setFilters, fetchTasks]);

  const handleFilterChange = (key, value) => {
    setFilters({ [key]: value });
    fetchTasks();
  };

  const handleResetFilters = () => {
    resetFilters();
    setSearchTerm('');
    fetchTasks();
  };

  const handleCreateTask = async (e) => {
    e.preventDefault();
    
    if (!formData.project) {
      toast.error('Veuillez sélectionner un projet');
      return;
    }

    const result = await createTask({
      ...formData,
      project: parseInt(formData.project),
    });

    if (result.success) {
      toast.success('Tâche créée');
      setIsModalOpen(false);
      setFormData({
        title: '',
        description: '',
        project: '',
        priority: 'medium',
        due_date: '',
        tag_ids: [],
      });
    } else {
      toast.error('Erreur lors de la création');
    }
  };

  const hasActiveFilters = filters.status || filters.priority || filters.project;

  if (isLoading && tasks.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Tâches</h1>
          <p className="text-gray-500 mt-1">Gérez toutes vos tâches</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <FiPlus />
          Nouvelle tâche
        </button>
      </div>

      {/* Search and Filters */}
      <div className="card p-4">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher une tâche..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10"
            />
          </div>

          {/* Filter toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`btn flex items-center gap-2 ${
              hasActiveFilters ? 'btn-primary' : 'btn-secondary'
            }`}
          >
            <FiFilter />
            Filtres
            {hasActiveFilters && (
              <span className="w-2 h-2 bg-white rounded-full" />
            )}
          </button>
        </div>

        {/* Filters */}
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="mt-4 pt-4 border-t border-gray-200"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="label">Projet</label>
                <select
                  value={filters.project}
                  onChange={(e) => handleFilterChange('project', e.target.value)}
                  className="input"
                >
                  <option value="">Tous les projets</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.title}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Statut</label>
                <select
                  value={filters.status}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                  className="input"
                >
                  <option value="">Tous les statuts</option>
                  <option value="todo">À faire</option>
                  <option value="in_progress">En cours</option>
                  <option value="review">En révision</option>
                  <option value="done">Terminé</option>
                </select>
              </div>
              <div>
                <label className="label">Priorité</label>
                <select
                  value={filters.priority}
                  onChange={(e) => handleFilterChange('priority', e.target.value)}
                  className="input"
                >
                  <option value="">Toutes les priorités</option>
                  <option value="low">Basse</option>
                  <option value="medium">Moyenne</option>
                  <option value="high">Haute</option>
                  <option value="urgent">Urgente</option>
                </select>
              </div>
            </div>
            {hasActiveFilters && (
              <div className="mt-4 flex justify-end">
                <button
                  onClick={handleResetFilters}
                  className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
                >
                  <FiX />
                  Réinitialiser les filtres
                </button>
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* Tasks Grid */}
      {tasks.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tasks.map((task, index) => (
            <motion.div
              key={task.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.03 }}
            >
              <Link to={`/tasks/${task.id}`}>
                <TaskCard task={task} />
              </Link>
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="card p-12 text-center">
          <FiCheckSquare className="mx-auto text-4xl text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">
            {hasActiveFilters || searchTerm ? 'Aucune tâche trouvée' : 'Aucune tâche'}
          </h3>
          <p className="text-gray-400 mb-4">
            {hasActiveFilters || searchTerm
              ? 'Essayez avec d\'autres filtres'
              : 'Créez votre première tâche'}
          </p>
          {!hasActiveFilters && !searchTerm && (
            <button
              onClick={() => setIsModalOpen(true)}
              className="btn btn-primary inline-flex items-center gap-2"
            >
              <FiPlus />
              Créer une tâche
            </button>
          )}
        </div>
      )}

      {/* Create Task Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Nouvelle tâche"
        size="lg"
      >
        <form onSubmit={handleCreateTask} className="space-y-4">
          <div>
            <label className="label">Titre *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="input"
              placeholder="Titre de la tâche"
              required
            />
          </div>
          <div>
            <label className="label">Projet *</label>
            <select
              value={formData.project}
              onChange={(e) => setFormData({ ...formData, project: e.target.value })}
              className="input"
              required
            >
              <option value="">Sélectionner un projet</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.title}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="input"
              rows={3}
              placeholder="Description de la tâche..."
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
              <label className="label">Date d'échéance</label>
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
                          tag_ids: formData.tag_ids.filter((id) => id !== tag.id),
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
              onClick={() => setIsModalOpen(false)}
              className="btn btn-secondary"
            >
              Annuler
            </button>
            <button type="submit" className="btn btn-primary">
              Créer
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Tasks;
