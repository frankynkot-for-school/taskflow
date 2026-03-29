import { memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiMessageSquare } from 'react-icons/fi';
import { useChatStore } from '../../store/chatStore';
import ChatPanel from './ChatPanel';

const ChatWidget = memo(() => {
  const { isOpen, toggleChat, isSending } = useChatStore();

  return (
    <>
      {/* Bouton flottant */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={toggleChat}
        className={`chat-button ${isOpen ? 'open' : ''}`}
        title="Ouvrir l'assistant IA"
      >
        <FiMessageSquare className="text-xl" />
        {isSending && (
          <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
        )}
      </motion.button>

      {/* Panel de chat */}
      <AnimatePresence>
        {isOpen && <ChatPanel />}
      </AnimatePresence>
    </>
  );
});

ChatWidget.displayName = 'ChatWidget';

export default ChatWidget;
