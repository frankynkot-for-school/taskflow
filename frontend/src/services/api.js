import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Instance Axios configurée
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token JWT
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Intercepteur pour gérer le rafraîchissement du token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });
          
          const { access } = response.data;
          localStorage.setItem('access_token', access);
          
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Services d'authentification
export const authService = {
  login: async (username, password) => {
    const response = await api.post('/auth/login/', { username, password });
    const { access, refresh } = response.data;
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    return response.data;
  },
  
  register: async (userData) => {
    const response = await api.post('/auth/register/', userData);
    return response.data;
  },
  
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/users/me/');
    return response.data;
  },
  
  updateProfile: async (userData) => {
    const response = await api.put('/users/update_profile/', userData);
    return response.data;
  },
};

// Services pour les projets
export const projectService = {
  getAll: async (params) => {
    const response = await api.get('/projects/', { params });
    return response.data;
  },
  
  getById: async (id) => {
    const response = await api.get(`/projects/${id}/`);
    return response.data;
  },
  
  create: async (data) => {
    const response = await api.post('/projects/', data);
    return response.data;
  },
  
  update: async (id, data) => {
    const response = await api.patch(`/projects/${id}/`, data);
    return response.data;
  },
  
  delete: async (id) => {
    await api.delete(`/projects/${id}/`);
  },
  
  addMember: async (id, userId) => {
    const response = await api.post(`/projects/${id}/add_member/`, { user_id: userId });
    return response.data;
  },
  
  removeMember: async (id, userId) => {
    const response = await api.post(`/projects/${id}/remove_member/`, { user_id: userId });
    return response.data;
  },
  
  getStatistics: async (id) => {
    const response = await api.get(`/projects/${id}/statistics/`);
    return response.data;
  },
};

// Services pour les tâches
export const taskService = {
  getAll: async (params) => {
    const response = await api.get('/tasks/', { params });
    return response.data;
  },
  
  getById: async (id) => {
    const response = await api.get(`/tasks/${id}/`);
    return response.data;
  },
  
  create: async (data) => {
    const response = await api.post('/tasks/', data);
    return response.data;
  },
  
  update: async (id, data) => {
    const response = await api.patch(`/tasks/${id}/`, data);
    return response.data;
  },
  
  delete: async (id) => {
    await api.delete(`/tasks/${id}/`);
  },
  
  changeStatus: async (id, status) => {
    const response = await api.post(`/tasks/${id}/change_status/`, { status });
    return response.data;
  },
  
  assign: async (id, userId) => {
    const response = await api.post(`/tasks/${id}/assign/`, { user_id: userId });
    return response.data;
  },
  
  getMyTasks: async () => {
    const response = await api.get('/tasks/my_tasks/');
    return response.data;
  },
  
  getOverdue: async () => {
    const response = await api.get('/tasks/overdue/');
    return response.data;
  },
  
  getDueToday: async () => {
    const response = await api.get('/tasks/due_today/');
    return response.data;
  },
  
  getDueThisWeek: async () => {
    const response = await api.get('/tasks/due_this_week/');
    return response.data;
  },
};

// Services pour les sous-tâches
export const subtaskService = {
  getAll: async (taskId) => {
    const response = await api.get('/subtasks/', { params: { task: taskId } });
    return response.data;
  },
  
  create: async (data) => {
    const response = await api.post('/subtasks/', data);
    return response.data;
  },
  
  update: async (id, data) => {
    const response = await api.patch(`/subtasks/${id}/`, data);
    return response.data;
  },
  
  delete: async (id) => {
    await api.delete(`/subtasks/${id}/`);
  },
  
  toggleComplete: async (id) => {
    const response = await api.post(`/subtasks/${id}/toggle_complete/`);
    return response.data;
  },
};

// Services pour les tags
export const tagService = {
  getAll: async () => {
    const response = await api.get('/tags/');
    return response.data;
  },
  
  create: async (data) => {
    const response = await api.post('/tags/', data);
    return response.data;
  },
  
  delete: async (id) => {
    await api.delete(`/tags/${id}/`);
  },
};

// Services pour les commentaires
export const commentService = {
  getAll: async (taskId) => {
    const response = await api.get('/comments/', { params: { task: taskId } });
    return response.data;
  },
  
  create: async (data) => {
    const response = await api.post('/comments/', data);
    return response.data;
  },
  
  update: async (id, data) => {
    const response = await api.patch(`/comments/${id}/`, data);
    return response.data;
  },
  
  delete: async (id) => {
    await api.delete(`/comments/${id}/`);
  },
};

// Services pour les pièces jointes
export const attachmentService = {
  upload: async (taskId, file) => {
    const formData = new FormData();
    formData.append('task', taskId);
    formData.append('file', file);
    
    const response = await api.post('/attachments/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  
  delete: async (id) => {
    await api.delete(`/attachments/${id}/`);
  },
};

// Services pour les utilisateurs
export const userService = {
  getAll: async (params) => {
    const response = await api.get('/users/', { params });
    return response.data;
  },
  
  search: async (query) => {
    const response = await api.get('/users/', { params: { search: query } });
    return response.data;
  },
};

// Service pour le dashboard
export const dashboardService = {
  getData: async () => {
    const response = await api.get('/dashboard/');
    return response.data;
  },
};

export default api;
