import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  Heart,
  MessageCircle,
  BookHeart,
  Wind,
  User,
  Shield,
  LogOut,
  Menu,
  X,
  Phone,
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { CrisisModal } from '../crisis';

/** Пункт навігації */
interface NavItem {
  to: string;
  label: string;
  icon: React.ElementType;
  adminOnly?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/chat', label: 'Чат', icon: MessageCircle },
  { to: '/emotions', label: 'Щоденник', icon: BookHeart },
  { to: '/breathing', label: 'Дихання', icon: Wind },
  { to: '/profile', label: 'Профіль', icon: User },
  { to: '/admin', label: 'Адмін', icon: Shield, adminOnly: true },
];

export default function Sidebar() {
  const { user, profile, logout } = useAuthStore();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [crisisOpen, setCrisisOpen] = useState(false);

  const isAdmin = user?.role === 'admin';
  const visibleItems = NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const linkClasses = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
      isActive
        ? 'bg-primary-50 text-primary-700 shadow-sm dark:bg-primary-900/30 dark:text-primary-300'
        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-800'
    }`;

  const sidebarContent = (
    <>
      {/* Logo */}
      <div className="p-4 pb-2">
        <NavLink to="/chat" className="flex items-center gap-2.5">
          <div className="w-9 h-9 bg-primary-100 dark:bg-primary-900/40 rounded-xl flex items-center justify-center">
            <Heart className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <span className="font-bold text-gray-800 dark:text-gray-100 text-sm">Emi</span>
            <p className="text-[10px] text-gray-400 dark:text-gray-500 leading-tight">Емоційна підтримка</p>
          </div>
        </NavLink>
      </div>

      {/* Nav links */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {visibleItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={linkClasses}
            onClick={() => setMobileOpen(false)}
          >
            <item.icon className="w-4.5 h-4.5 flex-shrink-0" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Crisis button */}
      <div className="px-3 pb-2">
        <button
          onClick={() => setCrisisOpen(true)}
          className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm
                     font-medium text-red-600 bg-red-50 hover:bg-red-100
                     dark:text-red-400 dark:bg-red-950/40 dark:hover:bg-red-900/50
                     transition-colors"
        >
          <Phone className="w-4 h-4" />
          Потрібна допомога
        </button>
      </div>

      {/* User info + logout */}
      <div className="border-t border-gray-100 dark:border-gray-800 p-3">
        <div className="flex items-center gap-2.5 px-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/40 flex items-center justify-center text-sm font-bold text-primary-700 dark:text-primary-300">
            {(profile?.nickname?.[0] || user?.email?.[0] || '?').toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-200 truncate">
              {profile?.nickname || 'Користувач'}
            </p>
            <p className="text-[11px] text-gray-400 dark:text-gray-500 truncate">
              {user?.email || ''}
            </p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm
                     text-gray-500 hover:text-gray-700 hover:bg-gray-50
                     dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-800
                     transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Вийти
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile toggle */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="lg:hidden fixed top-3 left-3 z-50 w-10 h-10 bg-white dark:bg-gray-900 shadow-md
                   rounded-xl flex items-center justify-center text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white"
        aria-label="Меню"
      >
        {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/30 z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-40 h-full w-60 bg-white dark:bg-gray-900 border-r border-gray-100 dark:border-gray-800
                    flex flex-col transition-transform duration-200
                    lg:translate-x-0 lg:static lg:z-auto
                    ${mobileOpen ? 'translate-x-0 shadow-xl' : '-translate-x-full'}`}
      >
        {sidebarContent}
      </aside>

      {/* Crisis Modal */}
      <CrisisModal open={crisisOpen} onClose={() => setCrisisOpen(false)} />
    </>
  );
}
