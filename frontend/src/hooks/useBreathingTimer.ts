import { useState, useCallback, useEffect, useRef } from 'react';
import type { BreathingPhase } from '../api/breathing';

export interface TimerState {
  /** Чи запущено таймер */
  running: boolean;
  /** Поточний цикл (1-based) */
  currentCycle: number;
  /** Поточний індекс фази */
  currentPhaseIndex: number;
  /** Поточна фаза */
  currentPhase: BreathingPhase | null;
  /** Секунди що залишились у поточній фазі */
  secondsLeft: number;
  /** Прогрес поточної фази (0..1) */
  phaseProgress: number;
  /** Чи завершена вправа */
  finished: boolean;
  /** Загальний прогрес вправи (0..1) */
  totalProgress: number;
}

interface UseBreathingTimerOptions {
  phases: BreathingPhase[];
  cycles: number;
  onComplete?: () => void;
  onPhaseChange?: (phase: BreathingPhase, cycle: number) => void;
}

export function useBreathingTimer({
  phases,
  cycles,
  onComplete,
  onPhaseChange,
}: UseBreathingTimerOptions) {
  const [running, setRunning] = useState(false);
  const [currentCycle, setCurrentCycle] = useState(1);
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState(0);
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [finished, setFinished] = useState(false);

  const intervalRef = useRef<ReturnType<typeof setInterval>>();
  const onCompleteRef = useRef(onComplete);
  const onPhaseChangeRef = useRef(onPhaseChange);

  // Update refs
  useEffect(() => {
    onCompleteRef.current = onComplete;
    onPhaseChangeRef.current = onPhaseChange;
  }, [onComplete, onPhaseChange]);

  const currentPhase = phases[currentPhaseIndex] || null;
  const phaseDuration = currentPhase?.duration_seconds || 1;
  const phaseProgress = currentPhase ? 1 - secondsLeft / phaseDuration : 0;

  // Total progress calculation
  const totalPhasesCount = phases.length * cycles;
  const completedPhases =
    (currentCycle - 1) * phases.length + currentPhaseIndex;
  const totalProgress = finished
    ? 1
    : (completedPhases + phaseProgress) / totalPhasesCount;

  const start = useCallback(() => {
    if (phases.length === 0) return;
    setRunning(true);
    setFinished(false);
    setCurrentCycle(1);
    setCurrentPhaseIndex(0);
    setSecondsLeft(phases[0].duration_seconds);
    onPhaseChangeRef.current?.(phases[0], 1);
  }, [phases]);

  const pause = useCallback(() => {
    setRunning(false);
  }, []);

  const resume = useCallback(() => {
    if (!finished) setRunning(true);
  }, [finished]);

  const reset = useCallback(() => {
    setRunning(false);
    setFinished(false);
    setCurrentCycle(1);
    setCurrentPhaseIndex(0);
    setSecondsLeft(phases[0]?.duration_seconds || 0);
    if (intervalRef.current) clearInterval(intervalRef.current);
  }, [phases]);

  // Timer tick
  useEffect(() => {
    if (!running) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }

    intervalRef.current = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev > 1) return prev - 1;

        // Фаза завершена — переходимо до наступної
        const nextPhaseIndex = currentPhaseIndex + 1;

        if (nextPhaseIndex < phases.length) {
          // Наступна фаза в поточному циклі
          setCurrentPhaseIndex(nextPhaseIndex);
          onPhaseChangeRef.current?.(phases[nextPhaseIndex], currentCycle);
          return phases[nextPhaseIndex].duration_seconds;
        }

        // Цикл завершений
        const nextCycle = currentCycle + 1;

        if (nextCycle <= cycles) {
          // Наступний цикл
          setCurrentCycle(nextCycle);
          setCurrentPhaseIndex(0);
          onPhaseChangeRef.current?.(phases[0], nextCycle);
          return phases[0].duration_seconds;
        }

        // Вправа завершена
        setRunning(false);
        setFinished(true);
        onCompleteRef.current?.();
        return 0;
      });
    }, 1000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [running, currentPhaseIndex, currentCycle, phases, cycles]);

  const state: TimerState = {
    running,
    currentCycle,
    currentPhaseIndex,
    currentPhase,
    secondsLeft,
    phaseProgress,
    finished,
    totalProgress,
  };

  return {
    ...state,
    start,
    pause,
    resume,
    reset,
  };
}

