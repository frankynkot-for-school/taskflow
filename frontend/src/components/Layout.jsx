import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiHome,
  FiCheckSquare,
  FiMenu,
  FiX,
  FiLogOut,
  FiUser,
  FiSettings,
  FiBell,
  FiGrid,
} from 'react-icons/fi';
import { useAuthStore } from '../store/authStore';
import { useWorkspaceStore } from '../store/workspaceStore';
import WorkspaceSwitcher from './WorkspaceSwitcher';
import ChatWidget from './chat/ChatWidget';

const Layout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const { user, logout } = useAuthStore();
  const { pendingInvitations } = useWorkspaceStore();
  const navigate = useNavigate();

  const navigation = [
    { name: 'Tableau de bord', href: '/dashboard', icon: FiHome },
    { name: 'Taches', href: '/tasks', icon: FiCheckSquare },
    { name: 'Workspaces', href: '/workspaces', icon: FiGrid },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-taskflow-background">
      <AnimatePresence mode="wait">
        {sidebarOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 256, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="bg-taskflow-sidebar border-r border-white/10 flex flex-col"
          >
            <div className="h-16 flex items-center justify-between px-6 border-b border-white/10">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-taskflow-primary rounded-lg flex items-center justify-center">
                  <FiCheckSquare className="text-white text-lg" />
                </div>
                <span className="font-bold text-xl text-white">TaskFlow</span>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="lg:hidden p-2 rounded-lg hover:bg-white/10"
              >
                <FiX className="text-white/80" />
              </button>
            </div>

            {/* Workspace Switcher */}
            <div className="border-b border-white/10">
              <WorkspaceSwitcher />
            </div>

            <nav className="flex-1 px-4 py-6 space-y-1">
              {navigation.map((item) => (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-taskflow-primaryLight text-taskflow-primary font-medium'
                        : 'text-white/80 hover:bg-white/10 hover:text-white'
                    }`
                  }
                >
                  <item.icon className="text-xl" />
                  <span>{item.name}</span>
                </NavLink>
              ))}
            </nav>

            <div className="p-4 border-t border-white/10">
              <div className="flex items-center gap-3 px-2">
                <div className="w-10 h-10 bg-taskflow-primaryLight rounded-full flex items-center justify-center">
                  <FiUser className="text-taskflow-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">
                    {user?.first_name || user?.username}
                  </p>
                  <p className="text-xs text-white/70 truncate">{user?.email}</p>
                </div>
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-taskflow-sidebar border-b border-white/10 flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 rounded-lg hover:bg-white/10"
              >
                <FiMenu className="text-white/80 text-xl" />
              </button>
            )}
            <h1 className="text-lg font-semibold text-white">
              Bienvenue, {user?.first_name || user?.username} !
            </h1>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/workspaces/invitations')}
              className="p-2 rounded-lg hover:bg-white/10 relative"
            >
              <FiBell className="text-white/80 text-xl" />
              {pendingInvitations.length > 0 && (
                <span className="absolute top-0 right-0 w-5 h-5 bg-taskflow-danger rounded-full text-xs text-white flex items-center justify-center">
                  {pendingInvitations.length}
                </span>
              )}
            </button>

            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2 p-2 rounded-lg hover:bg-white/10"
              >
                <div className="w-8 h-8 bg-taskflow-primaryLight rounded-full flex items-center justify-center">
                  <FiUser className="text-taskflow-primary" />
                </div>
              </button>

              <AnimatePresence>
                {userMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute right-0 mt-2 w-48 bg-taskflow-card rounded-lg shadow-lg border border-white/10 py-1 z-50"
                  >
                    <button
                      onClick={() => {
                        navigate('/settings');
                        setUserMenuOpen(false);
                      }}
                      className="w-full px-4 py-2 text-left text-white hover:bg-white/10 flex items-center gap-2"
                    >
                      <FiSettings className="text-white/60" />
                      Parametres
                    </button>
                    <hr className="my-1 border-white/10" />
                    <button
                      onClick={handleLogout}
                      className="w-full px-4 py-2 text-left text-taskflow-danger hover:bg-white/10 flex items-center gap-2"
                    >
                      <FiLogOut className="text-taskflow-danger" />
                      Deconnexion
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-auto p-6 bg-taskflow-content">
          <Outlet />
        </main>
      </div>

      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-taskflow-sidebar/70 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Chat Widget */}
      <ChatWidget />
    </div>
  );
};

export default Layout;
