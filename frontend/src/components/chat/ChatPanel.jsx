import { useState, useEffect, useRef, memo } from 'react';
import { motion } from 'framer-motion';
import {
  FiX,
  FiPlus,
  FiTrash2,
  FiArchive,
  FiMessageSquare,
  FiChevronLeft,
} from 'react-icons/fi';
import { useChatStore } from '../../store/chatStore';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import LoadingSpinner from '../LoadingSpinner';

const ChatPanel = memo(() => {
  const {
    conversations,
    currentConversation,
    messages,
    isLoading,
    isSending,
    error,
    closeChat,
    fetchConversations,
    selectConversation,
    startNewConversation,
    archiveConversation,
    deleteConversation,
  } = useChatStore();

  const [showConversationList, setShowConversationList] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSelectConversation = async (id) => {
    await selectConversation(id);
    setShowConversationList(false);
  };

  const handleNewConversation = () => {
    startNewConversation();
    setShowConversationList(false);
  };

  const handleArchive = async (id, e) => {
    e.stopPropagation();
    await archiveConversation(id);
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (window.confirm('Supprimer cette conversation ?')) {
      await deleteConversation(id);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      className="fixed bottom-24 right-6 w-96 h-[32rem] bg-white rounded-xl shadow-2xl border border-gray-200 flex flex-col z-50 overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-taskflow-primary text-white">
        <div className="flex items-center gap-2">
          {currentConversation && !showConversationList && (
            <button
              onClick={() => setShowConversationList(true)}
              className="p-1 rounded hover:bg-white/20"
            >
              <FiChevronLeft />
            </button>
          )}
          <FiMessageSquare />
          <h3 className="font-semibold">
            {showConversationList
              ? 'Conversations'
              : currentConversation?.title || 'Nouvelle conversation'}
          </h3>
        </div>
        <div className="flex items-center gap-1">
          {!showConversationList && (
            <button
              onClick={() => setShowConversationList(true)}
              className="p-2 rounded hover:bg-white/20"
              title="Historique"
            >
              <FiArchive />
            </button>
          )}
          <button
            onClick={handleNewConversation}
            className="p-2 rounded hover:bg-white/20"
            title="Nouvelle conversation"
          >
            <FiPlus />
          </button>
          <button
            onClick={closeChat}
            className="p-2 rounded hover:bg-white/20"
          >
            <FiX />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden bg-taskflow-background">
        {showConversationList ? (
          <div className="h-full overflow-y-auto p-3 space-y-2">
            {isLoading ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner size="md" />
              </div>
            ) : conversations.length > 0 ? (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => handleSelectConversation(conv.id)}
                  className={`p-3 rounded-lg cursor-pointer group transition-colors ${
                    currentConversation?.id === conv.id
                      ? 'bg-taskflow-primaryLight border border-taskflow-primary'
                      : 'bg-white hover:bg-gray-50 border border-gray-200'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-taskflow-sidebar truncate">
                        {conv.title || 'Sans titre'}
                      </p>
                      {conv.last_message && (
                        <p className="text-sm text-gray-500 truncate mt-1">
                          {conv.last_message.content}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => handleArchive(conv.id, e)}
                        className="p-1 rounded hover:bg-gray-200 text-gray-500"
                        title="Archiver"
                      >
                        <FiArchive className="text-sm" />
                      </button>
                      <button
                        onClick={(e) => handleDelete(conv.id, e)}
                        className="p-1 rounded hover:bg-red-100 text-taskflow-danger"
                        title="Supprimer"
                      >
                        <FiTrash2 className="text-sm" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8">
                <FiMessageSquare className="text-4xl text-gray-300 mx-auto mb-2" />
                <p className="text-gray-500">Aucune conversation</p>
                <button
                  onClick={handleNewConversation}
                  className="mt-3 text-taskflow-primary hover:underline text-sm"
                >
                  Commencer une nouvelle conversation
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex flex-col">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length > 0 ? (
                messages.map((message) => (
                  <ChatMessage key={message.id} message={message} />
                ))
              ) : (
                <div className="text-center py-8">
                  <FiMessageSquare className="text-4xl text-gray-300 mx-auto mb-2" />
                  <p className="text-gray-500 mb-1">Comment puis-je vous aider ?</p>
                  <p className="text-gray-400 text-sm">
                    Posez-moi des questions sur vos taches
                  </p>
                </div>
              )}
              {isSending && (
                <div className="flex items-center gap-2 text-gray-500">
                  <LoadingSpinner size="sm" />
                  <span className="text-sm">L'assistant reflechit...</span>
                </div>
              )}
              {error && (
                <div className="p-3 rounded-lg bg-red-50 text-taskflow-danger text-sm border border-red-200">
                  {error}
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      {!showConversationList && <ChatInput />}
    </motion.div>
  );
});

ChatPanel.displayName = 'ChatPanel';

export default ChatPanel;
