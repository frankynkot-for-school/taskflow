import { create } from 'zustand';
import { projectService, taskService, tagService, dashboardService } from '../services/api';

export const useProjectStore = create((set, get) => ({
  projects: [],
  currentProject: null,
  isLoading: false,
  error: null,

  // Récupérer tous les projets
  fetchProjects: async () => {
    set({ isLoading: true });
    try {
      const data = await projectService.getAll();
      set({ projects: data.results || data, isLoading: false });
    } catch (error) {
      set({ error: error.message, isLoading: false });
    }
  },

  // Récupérer un projet par ID
  fetchProject: async (id) => {
    set({ isLoading: true });
    try {
      const project = await projectService.getById(id);
      set({ currentProject: project, isLoading: false });
      return project;
    } catch (error) {
      set({ error: error.message, isLoading: false });
      return null;
    }
  },

  // Créer un projet
  createProject: async (data) => {
    try {
      const project = await projectService.create(data);
      set((state) => ({ projects: [project, ...state.projects] }));
      return { success: true, project };
    } catch (error) {
      return { success: false, error: error.response?.data };
    }
  },

  // Mettre à jour un projet
  updateProject: async (id, data) => {
    try {
      const project = await projectService.update(id, data);
      set((state) => ({
        projects: state.projects.map((p) => (p.id === id ? project : p)),
        currentProject: state.currentProject?.id === id ? project : state.currentProject,
      }));
      return { success: true, project };
    } catch (error) {
      return { success: false, error: error.response?.data };
    }
  },

  // Supprimer un projet
  deleteProject: async (id) => {
    try {
      await projectService.delete(id);
      set((state) => ({
        projects: state.projects.filter((p) => p.id !== id),
        currentProject: state.currentProject?.id === id ? null : state.currentProject,
      }));
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data };
    }
  },

  // Effacer le projet courant
  clearCurrentProject: () => set({ currentProject: null }),
}));

export const useTaskStore = create((set, get) => ({
  tasks: [],
  currentTask: null,
  isLoading: false,
  error: null,
  filters: {
    status: '',
    priority: '',
    project: '',
    search: '',
  },

  // Récupérer toutes les tâches
  fetchTasks: async (params = {}) => {
    set({ isLoading: true });
    try {
      const { filters } = get();
      const queryParams = { ...filters, ...params };
      // Nettoyer les paramètres vides
      Object.keys(queryParams).forEach((key) => {
        if (!queryParams[key]) delete queryParams[key];
      });
      
      const data = await taskService.getAll(queryParams);
      set({ tasks: data.results || data, isLoading: false });
    } catch (error) {
      set({ error: error.message, isLoading: false });
    }
  },

  // Récupérer une tâche par ID
  fetchTask: async (id) => {
    set({ isLoading: true });
    try {
      const task = await taskService.getById(id);
      set({ currentTask: task, isLoading: false });
      return task;
    } catch (error) {
      set({ error: error.message, isLoading: false });
      return null;
    }
  },

  // Créer une tâche
  createTask: async (data) => {
    try {
      const task = await taskService.create(data);
      set((state) => ({ tasks: [task, ...state.tasks] }));
      return { success: true, task };
    } catch (error) {
      return { success: false, error: error.response?.data };
    }
  },

  // Mettre à jour une tâche
  updateTask: async (id, data) => {
    try {
      const task = await taskService.update(id, data);
      set((state) => ({
        tasks: state.tasks.map((t) => (t.id === id ? { ...t, ...task } : t)),
        currentTask: state.currentTask?.id === id ? { ...state.currentTask, ...task } : state.currentTask,
      }));
      return { success: true, task };
    } catch (error) {
      return { success: false, error: error.response?.data };
    }
  },

  // Supprimer une tâche
  deleteTask: async (id) => {
    try {
      await taskService.delete(id);
      set((state) => ({
        tasks: state.tasks.filter((t) => t.id !== id),
        currentTask: state.currentTask?.id === id ? null : state.currentTask,
      }));
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data };
    }
  },

  // Changer le statut d'une tâche
  changeTaskStatus: async (id, status) => {
    try {
      const task = await taskService.changeStatus(id, status);
      set((state) => ({
        tasks: state.tasks.map((t) => (t.id === id ? { ...t, status } : t)),
        currentTask: state.currentTask?.id === id ? { ...state.currentTask, status } : state.currentTask,
      }));
      return { success: true, task };
    } catch (error) {
      return { success: false, error: error.response?.data };
    }
  },

  // Mettre à jour les filtres
  setFilters: (newFilters) => {
    set((state) => ({
      filters: { ...state.filters, ...newFilters },
    }));
  },

  // Réinitialiser les filtres
  resetFilters: () => {
    set({
      filters: {
        status: '',
        priority: '',
        project: '',
        search: '',
      },
    });
  },

  // Effacer la tâche courante
  clearCurrentTask: () => set({ currentTask: null }),
}));

export const useTagStore = create((set) => ({
  tags: [],
  isLoading: false,

  fetchTags: async () => {
    set({ isLoading: true });
    try {
      const data = await tagService.getAll();
      set({ tags: data.results || data, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
    }
  },

  createTag: async (data) => {
    try {
      const tag = await tagService.create(data);
      set((state) => ({ tags: [...state.tags, tag] }));
      return { success: true, tag };
    } catch (error) {
      return { success: false, error: error.response?.data };
    }
  },

  deleteTag: async (id) => {
    try {
      await tagService.delete(id);
      set((state) => ({ tags: state.tags.filter((t) => t.id !== id) }));
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data };
    }
  },
}));

export const useDashboardStore = create((set) => ({
  data: null,
  isLoading: false,

  fetchDashboard: async () => {
    set({ isLoading: true });
    try {
      const data = await dashboardService.getData();
      set({ data, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
    }
  },
}));
