import { useEffect, useState } from 'react';
import { Loader2, BarChart3, Users, Database, Activity } from 'lucide-react';
import { useAdminStore } from '../stores/adminStore';
import {
  StatsCards,
  CrisisBreakdown,
  UsersTable,
  SystemMonitor,
  KnowledgeManager,
} from '../components/admin';

type Tab = 'dashboard' | 'users' | 'knowledge' | 'monitoring';

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: 'dashboard', label: 'Дашборд', icon: BarChart3 },
  { id: 'users', label: 'Користувачі', icon: Users },
  { id: 'knowledge', label: 'База знань', icon: Database },
  { id: 'monitoring', label: 'Моніторинг', icon: Activity },
];

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');

  const {
    stats,
    statsLoading,
    health,
    healthLoading,
    fetchStats,
    fetchHealth,
    fetchUsers,
  } = useAdminStore();

  // Завантажуємо дані при монтуванні
  useEffect(() => {
    fetchStats();
    fetchHealth();
    fetchUsers();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="h-full">
      {/* Tabs */}
      <div className="border-b border-gray-100 bg-white/50">
        <div className="max-w-7xl mx-auto px-4 lg:px-6">
          <nav className="flex gap-1 -mb-px">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2
                  transition-colors
                  ${activeTab === tab.id
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 lg:px-6 py-6">
        {/* ── Dashboard Tab ── */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {statsLoading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
              </div>
            ) : stats ? (
              <>
                <StatsCards stats={stats} />

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <CrisisBreakdown crisis={stats.crisis} />

                  {health && (
                    <SystemMonitor
                      health={health}
                      loading={healthLoading}
                      onRefresh={fetchHealth}
                    />
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-16 text-gray-400">
                Не вдалося завантажити статистику
              </div>
            )}
          </div>
        )}

        {/* ── Users Tab ── */}
        {activeTab === 'users' && (
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-800">Управління користувачами</h2>
              <p className="text-sm text-gray-500">
                Перегляд, пошук та блокування акаунтів
              </p>
            </div>
            <UsersTable />
          </div>
        )}

        {/* ── Knowledge Tab ── */}
        {activeTab === 'knowledge' && (
          <div>
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-800">Управління базою знань</h2>
              <p className="text-sm text-gray-500">
                Завантаження та управління документами для RAG
              </p>
            </div>
            <KnowledgeManager />
          </div>
        )}

        {/* ── Monitoring Tab ── */}
        {activeTab === 'monitoring' && (
          <div className="space-y-6">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-800">Моніторинг системи</h2>
              <p className="text-sm text-gray-500">
                Стан компонентів та продуктивність
              </p>
            </div>

            {health ? (
              <SystemMonitor
                health={health}
                loading={healthLoading}
                onRefresh={fetchHealth}
              />
            ) : healthLoading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
              </div>
            ) : (
              <div className="text-center py-16 text-gray-400">
                Не вдалося завантажити дані моніторингу
              </div>
            )}

            {/* Quick stats in monitoring */}
            {stats && (
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-4">📊 Швидка статистика</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-gray-50 rounded-xl">
                    <p className="text-xl font-bold text-gray-800">{stats.total_users}</p>
                    <p className="text-xs text-gray-500">Користувачів</p>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-xl">
                    <p className="text-xl font-bold text-gray-800">{stats.total_conversations}</p>
                    <p className="text-xs text-gray-500">Розмов</p>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-xl">
                    <p className="text-xl font-bold text-gray-800">{stats.total_messages}</p>
                    <p className="text-xs text-gray-500">Повідомлень</p>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-xl">
                    <p className="text-xl font-bold text-orange-600">
                      {stats.crisis.total_crisis_messages}
                    </p>
                    <p className="text-xs text-gray-500">Кризових</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

