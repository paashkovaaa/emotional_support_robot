import { RefreshCw } from 'lucide-react';
import type { SystemHealth, ServiceHealth } from '../../types';

interface Props {
  health: SystemHealth;
  loading: boolean;
  onRefresh: () => void;
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; classes: string }> = {
    ok: { label: 'OK', classes: 'bg-green-100 text-green-700' },
    healthy: { label: 'Здоровий', classes: 'bg-green-100 text-green-700' },
    degraded: { label: 'Деградований', classes: 'bg-yellow-100 text-yellow-700' },
    unhealthy: { label: 'Нездоровий', classes: 'bg-red-100 text-red-700' },
    error: { label: 'Помилка', classes: 'bg-red-100 text-red-700' },
    unavailable: { label: 'Недоступний', classes: 'bg-gray-100 text-gray-500' },
  };

  const c = config[status] ?? { label: status, classes: 'bg-gray-100 text-gray-600' };

  return (
    <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${c.classes}`}>
      {c.label}
    </span>
  );
}

function ServiceRow({ name, service }: { name: string; service: ServiceHealth }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-50 last:border-b-0">
      <div className="flex items-center gap-3">
        <div
          className={`w-2.5 h-2.5 rounded-full ${
            service.status === 'ok'
              ? 'bg-green-500'
              : service.status === 'error'
                ? 'bg-red-500'
                : 'bg-gray-400'
          }`}
        />
        <span className="text-sm font-medium text-gray-700">{name}</span>
      </div>
      <div className="flex items-center gap-3">
        {service.latency_ms != null && (
          <span className="text-xs text-gray-400">{service.latency_ms} ms</span>
        )}
        {service.detail && (
          <span className="text-xs text-gray-400 max-w-[200px] truncate" title={service.detail}>
            {service.detail}
          </span>
        )}
        <StatusBadge status={service.status} />
      </div>
    </div>
  );
}

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);

  const parts: string[] = [];
  if (d > 0) parts.push(`${d}д`);
  if (h > 0) parts.push(`${h}год`);
  parts.push(`${m}хв`);
  return parts.join(' ');
}

export default function SystemMonitor({ health, loading, onRefresh }: Props) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
          🖥️ Стан системи
        </h3>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
          title="Оновити"
        >
          <RefreshCw className={`w-4 h-4 text-gray-500 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Overall status */}
      <div className="flex items-center justify-between mb-5 p-4 bg-gray-50 rounded-xl">
        <div>
          <p className="text-xs text-gray-500 mb-1">Загальний стан</p>
          <StatusBadge status={health.status} />
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500 mb-1">Uptime</p>
          <p className="text-sm font-medium text-gray-700">{formatUptime(health.uptime_seconds)}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500 mb-1">Версія</p>
          <p className="text-sm font-medium text-gray-700">v{health.version}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500 mb-1">Середовище</p>
          <p className="text-sm font-medium text-gray-700">{health.environment}</p>
        </div>
      </div>

      {/* Services */}
      <div>
        <ServiceRow name="PostgreSQL" service={health.database} />
        <ServiceRow name="Redis" service={health.redis} />
      </div>
    </div>
  );
}

