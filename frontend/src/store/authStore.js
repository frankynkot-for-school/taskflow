import { create } from 'zustand';
import { authService } from '../services/api';

export const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  // Initialiser l'authentification au chargement
  initialize: async () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        const user = await authService.getCurrentUser();
        set({ user, isAuthenticated: true, isLoading: false });
      } catch (error) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({ user: null, isAuthenticated: false, isLoading: false });
      }
    } else {
      set({ isLoading: false });
    }
  },

  // Connexion
  login: async (username, password) => {
    try {
      set({ error: null });
      await authService.login(username, password);
      const user = await authService.getCurrentUser();
      set({ user, isAuthenticated: true });
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || 'Identifiants incorrects';
      set({ error: message });
      return { success: false, error: message };
    }
  },

  // Inscription
  register: async (userData) => {
    try {
      set({ error: null });
      await authService.register(userData);
      return { success: true };
    } catch (error) {
      const message = error.response?.data || 'Erreur lors de l\'inscription';
      set({ error: message });
      return { success: false, error: message };
    }
  },

  // Déconnexion
  logout: () => {
    authService.logout();
    set({ user: null, isAuthenticated: false });
  },

  // Mettre à jour le profil
  updateProfile: async (userData) => {
    try {
      const user = await authService.updateProfile(userData);
      set({ user });
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data };
    }
  },

  // Effacer les erreurs
  clearError: () => set({ error: null }),
}));
