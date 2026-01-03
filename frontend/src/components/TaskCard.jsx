import { motion } from 'framer-motion';
import { FiCalendar, FiUser, FiMessageSquare, FiCheckSquare } from 'react-icons/fi';
import { format, isPast, isToday } from 'date-fns';
import { fr } from 'date-fns/locale';

const TaskCard = ({ task, onClick }) => {
  const statusStyles = {
    todo: 'bg-gray-100 text-gray-800',
    in_progress: 'bg-blue-100 text-blue-800',
    review: 'bg-yellow-100 text-yellow-800',
    done: 'bg-green-100 text-green-800',
  };

  const statusLabels = {
    todo: 'À faire',
    in_progress: 'En cours',
    review: 'En révision',
    done: 'Terminé',
  };

  const priorityStyles = {
    low: 'bg-gray-100 text-gray-600',
    medium: 'bg-blue-100 text-blue-600',
    high: 'bg-orange-100 text-orange-600',
    urgent: 'bg-red-100 text-red-600',
  };

  const priorityLabels = {
    low: 'Basse',
    medium: 'Moyenne',
    high: 'Haute',
    urgent: 'Urgente',
  };

  const isOverdue = task.due_date && isPast(new Date(task.due_date)) && task.status !== 'done';
  const isDueToday = task.due_date && isToday(new Date(task.due_date));

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      onClick={onClick}
      className="card p-4 hover:shadow-md transition-shadow cursor-pointer"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <h3 className="font-medium text-gray-800 line-clamp-2">{task.title}</h3>
        <span className={`px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap ${priorityStyles[task.priority]}`}>
          {priorityLabels[task.priority]}
        </span>
      </div>

      {/* Tags */}
      {task.tags && task.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {task.tags.slice(0, 3).map((tag) => (
            <span
              key={tag.id}
              className="px-2 py-0.5 rounded text-xs font-medium"
              style={{ backgroundColor: tag.color + '20', color: tag.color }}
            >
              {tag.name}
            </span>
          ))}
          {task.tags.length > 3 && (
            <span className="text-xs text-gray-500">+{task.tags.length - 3}</span>
          )}
        </div>
      )}

      {/* Progress bar pour les sous-tâches */}
      {task.subtasks_count > 0 && (
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
            <span className="flex items-center gap-1">
              <FiCheckSquare />
              Sous-tâches
            </span>
            <span>{task.subtasks_completed}/{task.subtasks_count}</span>
          </div>
          <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-500 rounded-full transition-all"
              style={{ width: `${task.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <div className="flex items-center gap-3">
          {/* Status */}
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusStyles[task.status]}`}>
            {statusLabels[task.status]}
          </span>

          {/* Date d'échéance */}
          {task.due_date && (
            <span
              className={`flex items-center gap-1 text-xs ${
                isOverdue
                  ? 'text-red-600'
                  : isDueToday
                  ? 'text-orange-600'
                  : 'text-gray-500'
              }`}
            >
              <FiCalendar />
              {format(new Date(task.due_date), 'dd MMM', { locale: fr })}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* Commentaires */}
          {task.comments_count > 0 && (
            <span className="flex items-center gap-1 text-xs text-gray-500">
              <FiMessageSquare />
              {task.comments_count}
            </span>
          )}

          {/* Assigné */}
          {task.assignee ? (
            <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center" title={task.assignee.username}>
              <span className="text-xs font-medium text-primary-600">
                {task.assignee.username.charAt(0).toUpperCase()}
              </span>
            </div>
          ) : (
            <div className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center" title="Non assigné">
              <FiUser className="text-gray-400 text-xs" />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default TaskCard;
