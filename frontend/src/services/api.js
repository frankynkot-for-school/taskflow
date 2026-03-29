import axios from 'axios';

const API_URL = '/api';

// Helper pour récupérer le workspace actuel depuis localStorage
const getCurrentWorkspaceId = () => {
  try {
    const workspaceState = localStorage.getItem('workspace-storage');
    if (workspaceState) {
      const parsed = JSON.parse(workspaceState);
      return parsed?.state?.currentWorkspace?.id || null;
    }
  } catch (e) {
    console.error('Error parsing workspace storage:', e);
  }
  return null;
};

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

// Services pour les tâches (hiérarchiques)
export const taskService = {
  getAll: async (params) => {
    const response = await api.get('/tasks/', { params });
    return response.data;
  },
  
  getRootTasks: async () => {
    const workspaceId = getCurrentWorkspaceId();
    const params = workspaceId ? { workspace: workspaceId } : {};
    const response = await api.get('/tasks/root_tasks/', { params });
    return response.data;
  },

  getChildren: async (id) => {
    const workspaceId = getCurrentWorkspaceId();
    const params = workspaceId ? { workspace: workspaceId } : {};
    const response = await api.get(`/tasks/${id}/children/`, { params });
    return response.data;
  },
  
  getById: async (id) => {
    const workspaceId = getCurrentWorkspaceId();
    const params = workspaceId ? { workspace: workspaceId } : {};
    const response = await api.get(`/tasks/${id}/`, { params });
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/tasks/', data);
    return response.data;
  },

  update: async (id, data) => {
    const workspaceId = getCurrentWorkspaceId();
    const params = workspaceId ? { workspace: workspaceId } : {};
    const response = await api.patch(`/tasks/${id}/`, data, { params });
    return response.data;
  },

  delete: async (id) => {
    const workspaceId = getCurrentWorkspaceId();
    const params = workspaceId ? { workspace: workspaceId } : {};
    await api.delete(`/tasks/${id}/`, { params });
  },

  changeStatus: async (id, status) => {
    const workspaceId = getCurrentWorkspaceId();
    const params = workspaceId ? { workspace: workspaceId } : {};
    const response = await api.post(`/tasks/${id}/change_status/`, { status }, { params });
    return response.data;
  },

  assign: async (id, userId) => {
    const workspaceId = getCurrentWorkspaceId();
    const params = workspaceId ? { workspace: workspaceId } : {};
    const response = await api.post(`/tasks/${id}/assign/`, { user_id: userId }, { params });
    return response.data;
  },
  
  getMyTasks: async () => {
    const workspaceId = getCurrentWorkspaceId();
    const params = workspaceId ? { workspace: workspaceId } : {};
    const response = await api.get('/tasks/my_tasks/', { params });
    return response.data;
  },

  getOverdue: async () => {
    const workspaceId = getCurrentWorkspaceId();
    const params = workspaceId ? { workspace: workspaceId } : {};
    const response = await api.get('/tasks/overdue/', { params });
    return response.data;
  },

  getDueToday: async () => {
    const workspaceId = getCurrentWorkspaceId();
    const params = workspaceId ? { workspace: workspaceId } : {};
    const response = await api.get('/tasks/due_today/', { params });
    return response.data;
  },
  
  getDueThisWeek: async () => {
    const response = await api.get('/tasks/due_this_week/');
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
  
  changeRole: async (userId, role) => {
    const response = await api.patch(`/users/${userId}/change_role/`, { role });
    return response.data;
  },
};

// Service pour le dashboard
export const dashboardService = {
  getData: async (params = {}) => {
    const response = await api.get('/dashboard/', { params });
    return response.data;
  },
};

// Service pour les activites
export const activityService = {
  getAll: async (params) => {
    const response = await api.get('/activities/', { params });
    return response.data;
  },

  getRecent: async () => {
    const response = await api.get('/activities/recent/');
    return response.data;
  },

  getByTask: async (taskId) => {
    const response = await api.get('/activities/', { params: { task: taskId } });
    return response.data;
  },
};

// Service pour les workspaces
export const workspaceService = {
  // CRUD de base
  getAll: async () => {
    const response = await api.get('/workspaces/');
    return response.data;
  },

  getMyWorkspaces: async () => {
    const response = await api.get('/workspaces/my_workspaces/');
    return response.data;
  },

  getCurrent: async () => {
    const response = await api.get('/workspaces/current/');
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/workspaces/${id}/`);
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/workspaces/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await api.patch(`/workspaces/${id}/`, data);
    return response.data;
  },

  delete: async (id) => {
    await api.delete(`/workspaces/${id}/`);
  },

  // Gestion des membres
  getMembers: async (id) => {
    const response = await api.get(`/workspaces/${id}/members/`);
    return response.data;
  },

  addMember: async (id, userId, role = 'member') => {
    const response = await api.post(`/workspaces/${id}/add_member/`, { user_id: userId, role });
    return response.data;
  },

  removeMember: async (id, userId) => {
    const response = await api.delete(`/workspaces/${id}/remove_member/`, { data: { user_id: userId } });
    return response.data;
  },

  updateMemberRole: async (id, userId, role) => {
    const response = await api.patch(`/workspaces/${id}/update_member_role/`, { user_id: userId, role });
    return response.data;
  },

  leave: async (id) => {
    const response = await api.post(`/workspaces/${id}/leave/`);
    return response.data;
  },

  transferOwnership: async (id, newOwnerId) => {
    const response = await api.post(`/workspaces/${id}/transfer_ownership/`, { new_owner_id: newOwnerId });
    return response.data;
  },
};

// Service pour les invitations
export const invitationService = {
  getAll: async () => {
    const response = await api.get('/invitations/');
    return response.data;
  },

  getPending: async () => {
    const response = await api.get('/invitations/pending/');
    return response.data;
  },

  getByToken: async (token) => {
    const response = await api.get('/invitations/by_token/', { params: { token } });
    return response.data;
  },

  create: async (data) => {
    const response = await api.post('/invitations/', data);
    return response.data;
  },

  accept: async (id) => {
    const response = await api.post(`/invitations/${id}/accept/`);
    return response.data;
  },

  decline: async (id) => {
    const response = await api.post(`/invitations/${id}/decline/`);
    return response.data;
  },

  resend: async (id) => {
    const response = await api.post(`/invitations/${id}/resend/`);
    return response.data;
  },

  cancel: async (id) => {
    await api.delete(`/invitations/${id}/cancel/`);
  },
};

// Service pour le chatbot
export const chatService = {
  // Lister les conversations
  getConversations: async () => {
    const workspaceId = getCurrentWorkspaceId();
    const params = workspaceId ? { workspace: workspaceId } : {};
    const response = await api.get('/chat/conversations/', { params });
    return response.data;
  },

  // Recuperer une conversation avec ses messages
  getConversation: async (id) => {
    const workspaceId = getCurrentWorkspaceId();
    const params = workspaceId ? { workspace: workspaceId } : {};
    const response = await api.get(`/chat/conversations/${id}/`, { params });
    return response.data;
  },

  // Envoyer un message
  sendMessage: async (message, conversationId = null) => {
    const workspaceId = getCurrentWorkspaceId();
    const data = { message };
    if (conversationId) {
      data.conversation_id = conversationId;
    }
    if (workspaceId) {
      data.workspace = workspaceId;
    }
    const response = await api.post('/chat/send/', data);
    return response.data;
  },

  // Archiver une conversation
  archiveConversation: async (id) => {
    const response = await api.post(`/chat/conversations/${id}/archive/`);
    return response.data;
  },

  // Supprimer une conversation
  deleteConversation: async (id) => {
    await api.delete(`/chat/conversations/${id}/`);
  },

  // Lister les conversations archivees
  getArchivedConversations: async () => {
    const workspaceId = getCurrentWorkspaceId();
    const params = workspaceId ? { workspace: workspaceId } : {};
    const response = await api.get('/chat/conversations/archived/', { params });
    return response.data;
  },
};

export default api;
