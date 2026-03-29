import { useState, useRef, useEffect, memo } from 'react';
import { FiSend } from 'react-icons/fi';
import { useChatStore } from '../../store/chatStore';

const ChatInput = memo(() => {
  const [input, setInput] = useState('');
  const { sendMessage, isSending } = useChatStore();
  const inputRef = useRef(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmedInput = input.trim();
    if (!trimmedInput || isSending) return;

    setInput('');
    await sendMessage(trimmedInput);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-3 border-t border-gray-200 bg-white"
    >
      <div className="flex items-end gap-2">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Posez votre question..."
          className="flex-1 resize-none bg-taskflow-background border border-gray-200 rounded-lg px-3 py-2 text-taskflow-sidebar placeholder-gray-400 focus:outline-none focus:border-taskflow-primary text-sm min-h-[40px] max-h-[120px]"
          rows={1}
          disabled={isSending}
        />
        <button
          type="submit"
          disabled={isSending || !input.trim()}
          className="p-2 rounded-lg bg-taskflow-primary text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-taskflow-primaryHover transition-colors"
        >
          <FiSend />
        </button>
      </div>
      <p className="text-xs text-gray-400 mt-2 text-center">
        L'assistant a acces a vos taches du workspace actuel
      </p>
    </form>
  );
});

ChatInput.displayName = 'ChatInput';

export default ChatInput;
