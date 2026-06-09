import type { CrisisStats } from '../../types';

interface Props {
  crisis: CrisisStats;
}

const LEVEL_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  low: { label: 'Низький', color: 'text-yellow-700', bg: 'bg-yellow-100' },
  medium: { label: 'Середній', color: 'text-orange-700', bg: 'bg-orange-100' },
  high: { label: 'Високий', color: 'text-red-600', bg: 'bg-red-100' },
  critical: { label: 'Критичний', color: 'text-red-800', bg: 'bg-red-200' },
};

export default function CrisisBreakdown({ crisis }: Props) {
  const total = crisis.total_crisis_messages;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
        ⚠️ Кризова статистика
      </h3>

      {total === 0 ? (
        <p className="text-sm text-gray-400 text-center py-4">
          Кризових повідомлень не зафіксовано
        </p>
      ) : (
        <div className="space-y-3">
          {Object.entries(LEVEL_CONFIG).map(([level, config]) => {
            const count = crisis.by_level[level] ?? 0;
            const pct = total > 0 ? Math.round((count / total) * 100) : 0;

            return (
              <div key={level}>
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-xs font-medium ${config.color}`}>
                    {config.label}
                  </span>
                  <span className="text-xs text-gray-500">
                    {count} ({pct}%)
                  </span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${config.bg}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

