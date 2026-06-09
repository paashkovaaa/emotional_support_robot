import { useEffect, useState } from 'react';
import { Loader2, Play, Pause, RotateCcw, CheckCircle2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { BreathingCircle, ExerciseCard } from '../components/breathing';
import { useBreathingTimer } from '../hooks/useBreathingTimer';
import * as breathingApi from '../api/breathing';
import type { BreathingExercise, BreathingExerciseShort } from '../api/breathing';

export default function BreathingPage() {
  const [exercises, setExercises] = useState<BreathingExerciseShort[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [activeExercise, setActiveExercise] = useState<BreathingExercise | null>(null);
  const [exerciseLoading, setExerciseLoading] = useState(false);

  // Завантажуємо список вправ
  useEffect(() => {
    breathingApi
      .getBreathingExercises()
      .then((data) => {
        setExercises(data);
        if (data.length > 0) setSelectedId(data[0].id);
      })
      .catch(() => toast.error('Не вдалося завантажити вправи'))
      .finally(() => setLoading(false));
  }, []);

  // Завантажуємо деталі вправи при виборі
  const handleSelectExercise = async (id: string) => {
    setSelectedId(id);
    timer.reset();
    setExerciseLoading(true);
    try {
      const exercise = await breathingApi.getBreathingExercise(id);
      setActiveExercise(exercise);
    } catch {
      toast.error('Не вдалося завантажити вправу');
    } finally {
      setExerciseLoading(false);
    }
  };

  // Timer
  const timer = useBreathingTimer({
    phases: activeExercise?.phases || [],
    cycles: activeExercise?.cycles || 1,
    onComplete: () => {
      toast.success('Чудово! Вправу завершено 🎉');
    },
  });

  // Auto-load first exercise details
  useEffect(() => {
    if (selectedId && !activeExercise) {
      handleSelectExercise(selectedId);
    }
  }, [selectedId]); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-5xl mx-auto px-4 lg:px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Exercise list */}
          <div className="lg:col-span-1 space-y-3">
            <h2 className="text-sm font-semibold text-gray-700 px-1">Оберіть вправу</h2>
            {exercises.map((ex) => (
              <ExerciseCard
                key={ex.id}
                exercise={ex}
                onSelect={handleSelectExercise}
                selected={ex.id === selectedId}
              />
            ))}
          </div>

          {/* Right: Animation + controls */}
          <div className="lg:col-span-2">
            {exerciseLoading ? (
              <div className="flex items-center justify-center py-24">
                <Loader2 className="w-8 h-8 text-primary-400 animate-spin" />
              </div>
            ) : activeExercise ? (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                {/* Exercise info */}
                <div className="text-center mb-6">
                  <h2 className="text-xl font-bold text-gray-800">
                    {activeExercise.name_uk}
                  </h2>
                  <p className="text-sm text-gray-500 mt-1 max-w-md mx-auto">
                    {activeExercise.description_uk}
                  </p>
                </div>

                {/* Animated circle */}
                <div className="flex justify-center mb-6">
                  <BreathingCircle
                    phase={timer.currentPhase?.phase as 'inhale' | 'hold' | 'exhale' | null}
                    label={timer.currentPhase?.label_uk || ''}
                    secondsLeft={timer.secondsLeft}
                    progress={timer.phaseProgress}
                    running={timer.running}
                  />
                </div>

                {/* Progress info */}
                <div className="text-center mb-4">
                  {timer.running && (
                    <p className="text-sm text-gray-500">
                      Цикл {timer.currentCycle} з {activeExercise.cycles}
                    </p>
                  )}
                  {timer.finished && (
                    <div className="flex items-center justify-center gap-2 text-green-600">
                      <CheckCircle2 className="w-5 h-5" />
                      <p className="text-sm font-medium">Вправу завершено! Чудова робота 💚</p>
                    </div>
                  )}
                </div>

                {/* Total progress bar */}
                {(timer.running || timer.finished) && (
                  <div className="mb-6 max-w-xs mx-auto">
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary-500 rounded-full transition-all duration-1000"
                        style={{ width: `${timer.totalProgress * 100}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Controls */}
                <div className="flex items-center justify-center gap-3">
                  {!timer.running && !timer.finished && (
                    <button
                      onClick={timer.start}
                      className="flex items-center gap-2 px-6 py-3 bg-primary-600 hover:bg-primary-700
                                 text-white font-medium rounded-xl text-sm transition-colors"
                    >
                      <Play className="w-4 h-4" />
                      Почати
                    </button>
                  )}

                  {timer.running && (
                    <button
                      onClick={timer.pause}
                      className="flex items-center gap-2 px-6 py-3 bg-gray-600 hover:bg-gray-700
                                 text-white font-medium rounded-xl text-sm transition-colors"
                    >
                      <Pause className="w-4 h-4" />
                      Пауза
                    </button>
                  )}

                  {!timer.running && !timer.finished && timer.secondsLeft > 0 && timer.currentCycle >= 1 && timer.currentPhaseIndex >= 0 && timer.secondsLeft < (activeExercise.phases[0]?.duration_seconds || 999) && (
                    <button
                      onClick={timer.resume}
                      className="flex items-center gap-2 px-6 py-3 bg-primary-600 hover:bg-primary-700
                                 text-white font-medium rounded-xl text-sm transition-colors"
                    >
                      <Play className="w-4 h-4" />
                      Продовжити
                    </button>
                  )}

                  {(timer.running || timer.finished) && (
                    <button
                      onClick={timer.reset}
                      className="flex items-center gap-2 px-4 py-3 bg-gray-100 hover:bg-gray-200
                                 text-gray-700 font-medium rounded-xl text-sm transition-colors"
                    >
                      <RotateCcw className="w-4 h-4" />
                      Заново
                    </button>
                  )}
                </div>

                {/* Phase legend */}
                <div className="mt-8 border-t border-gray-100 pt-4">
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                    Фази циклу
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {activeExercise.phases.map((phase, i) => (
                      <div
                        key={i}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm
                          ${timer.running && timer.currentPhaseIndex === i
                            ? 'bg-primary-50 text-primary-700 font-medium'
                            : 'bg-gray-50 text-gray-600'
                          }`}
                      >
                        <span>
                          {phase.phase === 'inhale' ? '💨' : phase.phase === 'hold' ? '⏸️' : '🌬️'}
                        </span>
                        <span>{phase.label_uk}</span>
                        <span className="text-xs text-gray-400">{phase.duration_seconds}с</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center py-24 text-gray-400">
                Оберіть вправу зі списку
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

