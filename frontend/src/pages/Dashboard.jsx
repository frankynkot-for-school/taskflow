import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  FiFolder,
  FiCheckSquare,
  FiClock,
  FiAlertCircle,
  FiTrendingUp,
  FiCalendar,
} from 'react-icons/fi';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import { useDashboardStore } from '../store/dataStore';
import LoadingSpinner from '../components/LoadingSpinner';
import TaskCard from '../components/TaskCard';

const Dashboard = () => {
  const { data, isLoading, fetchDashboard } = useDashboardStore();

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // Données pour les graphiques
  const statusChartData = [
    { name: 'À faire', value: data.tasks_by_status.todo, color: '#9CA3AF' },
    { name: 'En cours', value: data.tasks_by_status.in_progress, color: '#3B82F6' },
    { name: 'En révision', value: data.tasks_by_status.review, color: '#F59E0B' },
    { name: 'Terminé', value: data.tasks_by_status.done, color: '#22C55E' },
  ];

  const priorityChartData = [
    { name: 'Basse', value: data.tasks_by_priority.low },
    { name: 'Moyenne', value: data.tasks_by_priority.medium },
    { name: 'Haute', value: data.tasks_by_priority.high },
    { name: 'Urgente', value: data.tasks_by_priority.urgent },
  ];

  const stats = [
    {
      label: 'Projets',
      value: data.total_projects,
      icon: FiFolder,
      color: 'bg-blue-500',
      link: '/projects',
    },
    {
      label: 'Tâches totales',
      value: data.total_tasks,
      icon: FiCheckSquare,
      color: 'bg-green-500',
      link: '/tasks',
    },
    {
      label: "Aujourd'hui",
      value: data.tasks_due_today,
      icon: FiCalendar,
      color: 'bg-yellow-500',
      link: '/tasks?due=today',
    },
    {
      label: 'En retard',
      value: data.overdue_tasks,
      icon: FiAlertCircle,
      color: 'bg-red-500',
      link: '/tasks?overdue=true',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Link to={stat.link}>
              <div className="card p-6 hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">{stat.label}</p>
                    <p className="text-3xl font-bold text-gray-800 mt-1">{stat.value}</p>
                  </div>
                  <div className={`p-3 rounded-xl ${stat.color}`}>
                    <stat.icon className="text-white text-xl" />
                  </div>
                </div>
              </div>
            </Link>
          </motion.div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status Pie Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card p-6"
        >
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <FiTrendingUp className="text-primary-600" />
            Répartition par statut
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={statusChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {statusChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap justify-center gap-4 mt-4">
            {statusChartData.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm text-gray-600">
                  {item.name} ({item.value})
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Priority Bar Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="card p-6"
        >
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <FiClock className="text-primary-600" />
            Tâches par priorité
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={priorityChartData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* Recent Tasks & My Tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* My Assigned Tasks */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="card p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">Mes tâches assignées</h3>
            <Link to="/tasks?my_tasks=true" className="text-sm text-primary-600 hover:underline">
              Voir tout
            </Link>
          </div>
          <div className="space-y-3">
            {data.my_assigned_tasks.length > 0 ? (
              data.my_assigned_tasks.slice(0, 5).map((task) => (
                <Link key={task.id} to={`/tasks/${task.id}`}>
                  <TaskCard task={task} />
                </Link>
              ))
            ) : (
              <p className="text-gray-500 text-center py-8">
                Aucune tâche assignée pour le moment
              </p>
            )}
          </div>
        </motion.div>

        {/* Recent Tasks */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="card p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">Tâches récentes</h3>
            <Link to="/tasks" className="text-sm text-primary-600 hover:underline">
              Voir tout
            </Link>
          </div>
          <div className="space-y-3">
            {data.recent_tasks.length > 0 ? (
              data.recent_tasks.map((task) => (
                <Link key={task.id} to={`/tasks/${task.id}`}>
                  <TaskCard task={task} />
                </Link>
              ))
            ) : (
              <p className="text-gray-500 text-center py-8">
                Aucune tâche récente
              </p>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;
