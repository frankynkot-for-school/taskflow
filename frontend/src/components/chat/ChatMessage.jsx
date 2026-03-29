import { memo } from 'react';
import { motion } from 'framer-motion';
import { FiUser } from 'react-icons/fi';
import { CHAT_ROLES, ROLE_STYLES } from '../../constants/chatConstants';

const ChatMessage = memo(({ message }) => {
  const isUser = message.role === CHAT_ROLES.USER;

  // Formater le contenu avec markdown simple
  const formatContent = (content) => {
    let formatted = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    formatted = formatted.replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 rounded text-sm">$1</code>');
    formatted = formatted.replace(/\n/g, '<br />');
    return formatted;
  };

  // Formater l'heure
  const formatTime = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
          isUser
            ? 'bg-taskflow-primary'
            : 'bg-gradient-to-br from-purple-500 to-pink-500'
        }`}
      >
        {isUser ? (
          <FiUser className="text-white text-sm" />
        ) : (
          <span className="text-white text-sm font-bold">AI</span>
        )}
      </div>

      {/* Message bubble */}
      <div className={`max-w-[80%] ${isUser ? 'text-right' : 'text-left'}`}>
        <div
          className={`inline-block px-4 py-2 rounded-2xl ${ROLE_STYLES[message.role]} ${
            isUser ? 'rounded-tr-sm' : 'rounded-tl-sm'
          }`}
        >
          <div
            className="text-sm whitespace-pre-wrap"
            dangerouslySetInnerHTML={{ __html: formatContent(message.content) }}
          />
        </div>
        <p className="text-xs text-gray-400 mt-1 px-1">
          {formatTime(message.created_at)}
        </p>
      </div>
    </motion.div>
  );
});

ChatMessage.displayName = 'ChatMessage';

export default ChatMessage;
