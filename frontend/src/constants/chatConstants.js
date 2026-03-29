// Chat Message Roles
export const CHAT_ROLES = {
  SYSTEM: 'system',
  USER: 'user',
  ASSISTANT: 'assistant',
};

export const ROLE_LABELS = {
  [CHAT_ROLES.USER]: 'Vous',
  [CHAT_ROLES.ASSISTANT]: 'Assistant',
};

export const ROLE_STYLES = {
  [CHAT_ROLES.USER]: 'bg-taskflow-primary text-white',
  [CHAT_ROLES.ASSISTANT]: 'bg-taskflow-card text-taskflow-sidebar border border-gray-200',
};
