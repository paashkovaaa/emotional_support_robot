import { useState } from 'react';
import {
  Search,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  ShieldBan,
  ShieldCheck,
  Loader2,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAdminStore } from '../../stores/adminStore';
import type { AdminUser } from '../../types';

export default function UsersTable() {
  const {
    users,
    usersTotal,
    usersPage,
    usersPages,
    usersLoading,
    usersError,
    usersSearch,
    usersSortBy,
    usersSortOrder,
    setUsersPage,
    setUsersSearch,
    setUsersFilters,
    setUsersSort,
    blockUser,
  } = useAdminStore();

  const [searchInput, setSearchInput] = useState(usersSearch);
  const [blockingId, setBlockingId] = useState<string | null>(null);
  const [filterRole, setFilterRole] = useState<string>('all');
  const [filterBlocked, setFilterBlocked] = useState<string>('all');

  const handleSearch = () => {
    setUsersSearch(searchInput);
  };

  const handleFilterChange = (role: string, blocked: string) => {
    setFilterRole(role);
    setFilterBlocked(blocked);
    setUsersFilters({
      role: role === 'all' ? undefined : (role as 'user' | 'admin'),
      is_blocked: blocked === 'all' ? undefined : blocked === 'true',
    });
  };

  const handleSort = (field: string) => {
    const newOrder = usersSortBy === field && usersSortOrder === 'asc' ? 'desc' : 'asc';
    setUsersSort(field, newOrder);
  };

  const handleBlock = async (user: AdminUser) => {
    const action = user.is_blocked ? 'розблокувати' : 'заблокувати';
    const confirmed = window.confirm(
      `${action.charAt(0).toUpperCase() + action.slice(1)} ${user.email ?? user.id}?`,
    );
    if (!confirmed) return;

    setBlockingId(user.id);
    try {
      const message = await blockUser(user.id, !user.is_blocked);
      toast.success(message);
    } catch {
      toast.error(`Не вдалося ${action} користувача`);
    } finally {
      setBlockingId(null);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('uk-UA', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const SortButton = ({ field, children }: { field: string; children: React.ReactNode }) => (
    <button
      onClick={() => handleSort(field)}
      className="flex items-center gap-1 text-xs font-medium text-gray-500 hover:text-gray-700 transition-colors"
    >
      {children}
      <ArrowUpDown className={`w-3 h-3 ${usersSortBy === field ? 'text-primary-600' : ''}`} />
    </button>
  );

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
      {/* Toolbar */}
      <div className="p-5 border-b border-gray-100">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Пошук за email..."
              className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm
                         focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-transparent"
            />
          </div>

          {/* Role filter */}
          <select
            value={filterRole}
            onChange={(e) => handleFilterChange(e.target.value, filterBlocked)}
            className="px-3 py-2.5 border border-gray-200 rounded-xl text-sm bg-white
                       focus:outline-none focus:ring-2 focus:ring-primary-400"
          >
            <option value="all">Всі ролі</option>
            <option value="user">Користувач</option>
            <option value="admin">Адмін</option>
          </select>

          {/* Blocked filter */}
          <select
            value={filterBlocked}
            onChange={(e) => handleFilterChange(filterRole, e.target.value)}
            className="px-3 py-2.5 border border-gray-200 rounded-xl text-sm bg-white
                       focus:outline-none focus:ring-2 focus:ring-primary-400"
          >
            <option value="all">Всі статуси</option>
            <option value="false">Активні</option>
            <option value="true">Заблоковані</option>
          </select>
        </div>
      </div>

      {/* Error */}
      {usersError && (
        <div className="px-5 py-3 bg-red-50 text-red-700 text-sm">{usersError}</div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left px-5 py-3">
                <SortButton field="email">Email</SortButton>
              </th>
              <th className="text-left px-5 py-3">
                <SortButton field="role">Роль</SortButton>
              </th>
              <th className="text-left px-5 py-3">
                <span className="text-xs font-medium text-gray-500">Статус</span>
              </th>
              <th className="text-left px-5 py-3">
                <span className="text-xs font-medium text-gray-500">Розмови</span>
              </th>
              <th className="text-left px-5 py-3">
                <SortButton field="last_login">Останній вхід</SortButton>
              </th>
              <th className="text-left px-5 py-3">
                <SortButton field="created_at">Реєстрація</SortButton>
              </th>
              <th className="text-right px-5 py-3">
                <span className="text-xs font-medium text-gray-500">Дії</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {usersLoading ? (
              <tr>
                <td colSpan={7} className="text-center py-12">
                  <Loader2 className="w-6 h-6 text-primary-400 animate-spin mx-auto mb-2" />
                  <p className="text-sm text-gray-500">Завантаження...</p>
                </td>
              </tr>
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-12 text-sm text-gray-400">
                  Користувачів не знайдено
                </td>
              </tr>
            ) : (
              users.map((user) => (
                <tr
                  key={user.id}
                  className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors"
                >
                  <td className="px-5 py-3">
                    <span className="text-sm text-gray-800 font-medium">
                      {user.email ?? '—'}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium
                        ${user.role === 'admin'
                          ? 'bg-purple-100 text-purple-700'
                          : 'bg-gray-100 text-gray-600'
                        }`}
                    >
                      {user.role === 'admin' ? '👑 Адмін' : 'Користувач'}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    {user.is_blocked ? (
                      <span className="inline-flex items-center gap-1 text-xs text-red-600 font-medium">
                        <ShieldBan className="w-3.5 h-3.5" />
                        Заблокований
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs text-green-600 font-medium">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        Активний
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-sm text-gray-600">
                    {user.conversations_count}
                  </td>
                  <td className="px-5 py-3 text-xs text-gray-500">
                    {formatDate(user.last_login)}
                  </td>
                  <td className="px-5 py-3 text-xs text-gray-500">
                    {formatDate(user.created_at)}
                  </td>
                  <td className="px-5 py-3 text-right">
                    {user.role !== 'admin' && (
                      <button
                        onClick={() => handleBlock(user)}
                        disabled={blockingId === user.id}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
                          disabled:opacity-50 disabled:cursor-not-allowed
                          ${user.is_blocked
                            ? 'bg-green-50 text-green-700 hover:bg-green-100'
                            : 'bg-red-50 text-red-700 hover:bg-red-100'
                          }`}
                      >
                        {blockingId === user.id
                          ? '...'
                          : user.is_blocked
                            ? 'Розблокувати'
                            : 'Заблокувати'}
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {usersPages > 1 && (
        <div className="flex items-center justify-between px-5 py-4 border-t border-gray-100">
          <p className="text-xs text-gray-500">
            Показано {users.length} з {usersTotal}
          </p>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setUsersPage(usersPage - 1)}
              disabled={usersPage <= 1}
              className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4 text-gray-600" />
            </button>

            <span className="text-sm text-gray-700 px-2">
              {usersPage} / {usersPages}
            </span>

            <button
              onClick={() => setUsersPage(usersPage + 1)}
              disabled={usersPage >= usersPages}
              className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4 text-gray-600" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

