interface BreathingCircleProps {
  /** Поточна фаза: inhale | hold | exhale */
  phase: 'inhale' | 'hold' | 'exhale' | null;
  /** Текст у центрі (назва фази українською) */
  label: string;
  /** Секунди що залишились */
  secondsLeft: number;
  /** Прогрес фази 0..1 */
  progress: number;
  /** Чи запущено */
  running: boolean;
}

/**
 * Анімоване коло для дихальних вправ.
 *
 * - inhale: коло збільшується
 * - exhale: коло зменшується
 * - hold: коло пульсує
 */
export default function BreathingCircle({
  phase,
  label,
  secondsLeft,
  progress,
  running,
}: BreathingCircleProps) {
  // Масштаб кола залежно від фази
  const getScale = () => {
    if (!running || !phase) return 0.6;
    if (phase === 'inhale') return 0.5 + progress * 0.5; // 0.5 → 1.0
    if (phase === 'exhale') return 1.0 - progress * 0.5;  // 1.0 → 0.5
    // hold — фіксований
    return 0.85;
  };

  // Колір залежно від фази
  const getColors = () => {
    if (!phase || !running) {
      return {
        bg: 'bg-gray-100',
        ring: 'ring-gray-200',
        text: 'text-gray-400',
        glow: '',
      };
    }
    switch (phase) {
      case 'inhale':
        return {
          bg: 'bg-blue-50',
          ring: 'ring-blue-300',
          text: 'text-blue-600',
          glow: 'shadow-[0_0_40px_rgba(59,130,246,0.3)]',
        };
      case 'hold':
        return {
          bg: 'bg-amber-50',
          ring: 'ring-amber-300',
          text: 'text-amber-600',
          glow: 'shadow-[0_0_40px_rgba(245,158,11,0.3)]',
        };
      case 'exhale':
        return {
          bg: 'bg-green-50',
          ring: 'ring-green-300',
          text: 'text-green-600',
          glow: 'shadow-[0_0_40px_rgba(34,197,94,0.3)]',
        };
    }
  };

  const scale = getScale();
  const colors = getColors();

  return (
    <div className="relative flex items-center justify-center" style={{ width: 280, height: 280 }}>
      {/* Outer ring (static) */}
      <div className="absolute w-full h-full rounded-full border-2 border-dashed border-gray-200 opacity-30" />

      {/* Animated circle */}
      <div
        className={`rounded-full ring-4 ${colors.bg} ${colors.ring} ${colors.glow}
                    flex flex-col items-center justify-center
                    transition-all duration-1000 ease-in-out`}
        style={{
          width: `${scale * 240}px`,
          height: `${scale * 240}px`,
        }}
      >
        {/* Phase label */}
        <p className={`text-lg font-bold ${colors.text} transition-colors duration-500`}>
          {running ? label : 'Готово?'}
        </p>

        {/* Timer */}
        {running && (
          <p className={`text-4xl font-bold ${colors.text} mt-1 tabular-nums`}>
            {secondsLeft}
          </p>
        )}
      </div>

      {/* SVG progress ring */}
      {running && (
        <svg
          className="absolute w-full h-full -rotate-90"
          viewBox="0 0 280 280"
        >
          <circle
            cx="140"
            cy="140"
            r="132"
            fill="none"
            stroke="currentColor"
            strokeWidth="4"
            className={colors.text}
            strokeLinecap="round"
            strokeDasharray={`${2 * Math.PI * 132}`}
            strokeDashoffset={`${2 * Math.PI * 132 * (1 - progress)}`}
            style={{ transition: 'stroke-dashoffset 1s linear' }}
            opacity={0.3}
          />
        </svg>
      )}
    </div>
  );
}

