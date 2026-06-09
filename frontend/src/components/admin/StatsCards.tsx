import {
  Users,
  MessageSquare,
  BookHeart,
  AlertTriangle,
  UserPlus,
  ShieldAlert,
  MessagesSquare,
  Activity,
} from 'lucide-react';
import type { SystemStats } from '../../types';

interface Props {
  stats: SystemStats;
}

export default function StatsCards({ stats }: Props) {
  const cards = [
    {
      label: 'Всього користувачів',
      value: stats.total_users,
      icon: Users,
      color: 'text-blue-600 bg-blue-100',
    },
    {
      label: 'Активні',
      value: stats.active_users,
      icon: Activity,
      color: 'text-green-600 bg-green-100',
    },
    {
      label: 'Заблоковані',
      value: stats.blocked_users,
      icon: ShieldAlert,
      color: 'text-red-600 bg-red-100',
    },
    {
      label: 'Розмови',
      value: stats.total_conversations,
      sub: `${stats.active_conversations} активних`,
      icon: MessagesSquare,
      color: 'text-indigo-600 bg-indigo-100',
    },
    {
      label: 'Повідомлення',
      value: stats.total_messages,
      icon: MessageSquare,
      color: 'text-purple-600 bg-purple-100',
    },
    {
      label: 'Записи емоцій',
      value: stats.total_emotion_entries,
      icon: BookHeart,
      color: 'text-pink-600 bg-pink-100',
    },
    {
      label: 'Кризові повідомлення',
      value: stats.crisis.total_crisis_messages,
      icon: AlertTriangle,
      color: 'text-orange-600 bg-orange-100',
    },
    {
      label: 'Нових за 7 днів',
      value: stats.users_registered_last_7_days,
      sub: `за 30 днів: ${stats.users_registered_last_30_days}`,
      icon: UserPlus,
      color: 'text-teal-600 bg-teal-100',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 flex items-start gap-4"
        >
          <div className={`p-3 rounded-xl ${card.color}`}>
            <card.icon className="w-5 h-5" />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-800">{card.value.toLocaleString()}</p>
            <p className="text-sm text-gray-500 mt-0.5">{card.label}</p>
            {card.sub && (
              <p className="text-xs text-gray-400 mt-1">{card.sub}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

