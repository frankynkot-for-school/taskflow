import { create } from 'zustand';
import { chatService } from '../services/api';

export const useChatStore = create((set, get) => ({
  // State
  conversations: [],
  currentConversation: null,
  messages: [],
  isOpen: false,
  isLoading: false,
  isSending: false,
  error: null,

  // Ouvrir/fermer le chat
  toggleChat: () => set((state) => ({ isOpen: !state.isOpen })),
  openChat: () => set({ isOpen: true }),
  closeChat: () => set({ isOpen: false }),

  // Charger les conversations
  fetchConversations: async () => {
    set({ isLoading: true, error: null });
    try {
      const conversations = await chatService.getConversations();
      set({ conversations: conversations.results || conversations, isLoading: false });
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Erreur de chargement', isLoading: false });
    }
  },

  // Charger une conversation specifique
  fetchConversation: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const conversation = await chatService.getConversation(id);
      set({
        currentConversation: conversation,
        messages: conversation.messages || [],
        isLoading: false,
      });
      return conversation;
    } catch (error) {
      set({ error: error.response?.data?.detail || 'Erreur de chargement', isLoading: false });
      return null;
    }
  },

  // Envoyer un message
  sendMessage: async (content) => {
    const { currentConversation, messages } = get();

    // Ajouter le message utilisateur localement pour un retour immediat
    const tempUserMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };
    set({
      messages: [...messages, tempUserMessage],
      isSending: true,
      error: null,
    });

    try {
      const response = await chatService.sendMessage(
        content,
        currentConversation?.id
      );

      // Mettre a jour avec la vraie reponse
      const assistantMessage = response.message;

      set((state) => {
        // Retirer le message temporaire et ajouter les vrais messages
        const filteredMessages = state.messages.filter(
          (m) => !String(m.id).startsWith('temp-')
        );

        return {
          currentConversation: state.currentConversation || {
            id: response.conversation_id,
            title: '',
          },
          messages: [
            ...filteredMessages,
            { ...tempUserMessage, id: response.user_message_id || tempUserMessage.id },
            assistantMessage,
          ],
          isSending: false,
        };
      });

      // Si nouvelle conversation, rafraichir la liste
      if (!currentConversation) {
        get().fetchConversations();
      }

      return { success: true, response };
    } catch (error) {
      set({
        isSending: false,
        error: error.response?.data?.error || "Erreur lors de l'envoi",
        // Retirer le message temporaire en cas d'erreur
        messages: get().messages.filter((m) => !String(m.id).startsWith('temp-')),
      });
      return { success: false, error };
    }
  },

  // Nouvelle conversation
  startNewConversation: () => {
    set({
      currentConversation: null,
      messages: [],
      error: null,
    });
  },

  // Selectionner une conversation
  selectConversation: async (id) => {
    await get().fetchConversation(id);
  },

  // Archiver une conversation
  archiveConversation: async (id) => {
    try {
      await chatService.archiveConversation(id);
      set((state) => ({
        conversations: state.conversations.filter((c) => c.id !== id),
        currentConversation:
          state.currentConversation?.id === id ? null : state.currentConversation,
        messages: state.currentConversation?.id === id ? [] : state.messages,
      }));
      return { success: true };
    } catch (error) {
      return { success: false, error };
    }
  },

  // Supprimer une conversation
  deleteConversation: async (id) => {
    try {
      await chatService.deleteConversation(id);
      set((state) => ({
        conversations: state.conversations.filter((c) => c.id !== id),
        currentConversation:
          state.currentConversation?.id === id ? null : state.currentConversation,
        messages: state.currentConversation?.id === id ? [] : state.messages,
      }));
      return { success: true };
    } catch (error) {
      return { success: false, error };
    }
  },

  // Reset (deconnexion)
  reset: () => {
    set({
      conversations: [],
      currentConversation: null,
      messages: [],
      isOpen: false,
      isLoading: false,
      isSending: false,
      error: null,
    });
  },
}));
