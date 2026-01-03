import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FiPlus, FiFolder, FiUsers, FiSearch, FiMoreVertical, FiEdit, FiTrash2 } from 'react-icons/fi';
import { useProjectStore } from '../store/dataStore';
import Modal from '../components/Modal';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';

const Projects = () => {
  const { projects, isLoading, fetchProjects, createProject, updateProject, deleteProject } = useProjectStore();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({
    title: '',
    description: '',
  });

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const filteredProjects = projects.filter((project) =>
    project.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleOpenModal = (project = null) => {
    if (project) {
      setEditingProject(project);
      setFormData({
        title: project.title,
        description: project.description || '',
      });
    } else {
      setEditingProject(null);
      setFormData({ title: '', description: '' });
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingProject(null);
    setFormData({ title: '', description: '' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (editingProject) {
      const result = await updateProject(editingProject.id, formData);
      if (result.success) {
        toast.success('Projet mis à jour');
        handleCloseModal();
      } else {
        toast.error('Erreur lors de la mise à jour');
      }
    } else {
      const result = await createProject(formData);
      if (result.success) {
        toast.success('Projet créé avec succès');
        handleCloseModal();
      } else {
        toast.error('Erreur lors de la création');
      }
    }
  };

  const handleDelete = async (project) => {
    if (window.confirm(`Supprimer le projet "${project.title}" ?`)) {
      const result = await deleteProject(project.id);
      if (result.success) {
        toast.success('Projet supprimé');
      } else {
        toast.error('Erreur lors de la suppression');
      }
    }
  };

  if (isLoading && projects.length === 0) {
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
          <h1 className="text-2xl font-bold text-gray-800">Projets</h1>
          <p className="text-gray-500 mt-1">Gérez vos projets et leurs tâches</p>
        </div>
        <button
          onClick={() => handleOpenModal()}
          className="btn btn-primary flex items-center gap-2"
        >
          <FiPlus />
          Nouveau projet
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Rechercher un projet..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="input pl-10"
        />
      </div>

      {/* Projects Grid */}
      {filteredProjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project, index) => (
            <motion.div
              key={project.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <ProjectCard
                project={project}
                onEdit={() => handleOpenModal(project)}
                onDelete={() => handleDelete(project)}
              />
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="card p-12 text-center">
          <FiFolder className="mx-auto text-4xl text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-600 mb-2">
            {searchTerm ? 'Aucun projet trouvé' : 'Aucun projet'}
          </h3>
          <p className="text-gray-400 mb-4">
            {searchTerm
              ? 'Essayez avec un autre terme de recherche'
              : 'Créez votre premier projet pour commencer'}
          </p>
          {!searchTerm && (
            <button
              onClick={() => handleOpenModal()}
              className="btn btn-primary inline-flex items-center gap-2"
            >
              <FiPlus />
              Créer un projet
            </button>
          )}
        </div>
      )}

      {/* Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingProject ? 'Modifier le projet' : 'Nouveau projet'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Titre *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="input"
              placeholder="Nom du projet"
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
              placeholder="Description du projet..."
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={handleCloseModal} className="btn btn-secondary">
              Annuler
            </button>
            <button type="submit" className="btn btn-primary">
              {editingProject ? 'Mettre à jour' : 'Créer'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

// Composant ProjectCard
const ProjectCard = ({ project, onEdit, onDelete }) => {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="card p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <Link to={`/projects/${project.id}`} className="flex-1">
          <h3 className="font-semibold text-gray-800 hover:text-primary-600 transition-colors">
            {project.title}
          </h3>
        </Link>
        <div className="relative">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="p-1 rounded hover:bg-gray-100"
          >
            <FiMoreVertical className="text-gray-400" />
          </button>
          {menuOpen && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setMenuOpen(false)}
              />
              <div className="absolute right-0 mt-1 w-32 bg-white rounded-lg shadow-lg border z-20 py-1">
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    onEdit();
                  }}
                  className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                >
                  <FiEdit className="text-gray-400" />
                  Modifier
                </button>
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    onDelete();
                  }}
                  className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                >
                  <FiTrash2 className="text-red-400" />
                  Supprimer
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Description */}
      {project.description && (
        <p className="text-sm text-gray-500 mb-4 line-clamp-2">
          {project.description}
        </p>
      )}

      {/* Progress */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm mb-1">
          <span className="text-gray-500">Progression</span>
          <span className="font-medium text-gray-700">{project.progress}%</span>
        </div>
        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-primary-500 rounded-full transition-all"
            style={{ width: `${project.progress}%` }}
          />
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span className="flex items-center gap-1">
            <FiFolder className="text-gray-400" />
            {project.tasks_count} tâches
          </span>
          <span className="flex items-center gap-1">
            <FiUsers className="text-gray-400" />
            {project.members_count}
          </span>
        </div>
        <Link
          to={`/projects/${project.id}`}
          className="text-sm text-primary-600 hover:underline"
        >
          Voir →
        </Link>
      </div>
    </div>
  );
};

export default Projects;
