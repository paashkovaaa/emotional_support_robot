import { Clock } from 'lucide-react';
import type { BreathingExerciseShort } from '../../api/breathing';

interface ExerciseCardProps {
  exercise: BreathingExerciseShort;
  onSelect: (id: string) => void;
  selected?: boolean;
}

const DIFFICULTY_MAP: Record<string, { label: string; color: string }> = {
  easy: { label: 'Легка', color: 'text-green-600 bg-green-50' },
  medium: { label: 'Середня', color: 'text-amber-600 bg-amber-50' },
  hard: { label: 'Складна', color: 'text-red-600 bg-red-50' },
};

export default function ExerciseCard({ exercise, onSelect, selected }: ExerciseCardProps) {
  const diff = DIFFICULTY_MAP[exercise.difficulty] || DIFFICULTY_MAP.easy;
  const minutes = Math.ceil(exercise.total_duration_seconds / 60);

  return (
    <button
      onClick={() => onSelect(exercise.id)}
      className={`w-full text-left p-4 rounded-2xl border-2 transition-all
        ${selected
          ? 'border-primary-500 bg-primary-50 shadow-sm'
          : 'border-gray-100 bg-white hover:border-gray-200 hover:shadow-sm'
        }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className={`font-semibold text-sm ${selected ? 'text-primary-700' : 'text-gray-800'}`}>
            {exercise.name_uk}
          </h3>
          <p className="text-xs text-gray-500 mt-1 line-clamp-2">
            {exercise.description_uk}
          </p>
        </div>
        <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${diff.color} flex-shrink-0`}>
          {diff.label}
        </span>
      </div>

      <div className="flex items-center gap-3 mt-3">
        <div className="flex items-center gap-1 text-xs text-gray-400">
          <Clock className="w-3 h-3" />
          <span>~{minutes} хв</span>
        </div>
        <div className="flex items-center gap-1 text-xs text-gray-400">
          <span>🔄</span>
          <span>{exercise.cycles} циклів</span>
        </div>
      </div>

      {exercise.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2.5">
          {exercise.tags.map((tag) => (
            <span
              key={tag}
              className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}
    </button>
  );
}


