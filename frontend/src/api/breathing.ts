import client from './client';

/* ── Types ── */

export interface BreathingPhase {
  phase: 'inhale' | 'hold' | 'exhale';
  label_uk: string;
  duration_seconds: number;
}

export interface BreathingExercise {
  id: string;
  name_uk: string;
  description_uk: string;
  phases: BreathingPhase[];
  cycles: number;
  total_duration_seconds: number;
  difficulty: 'easy' | 'medium' | 'hard';
  tags: string[];
}

export interface BreathingExerciseShort {
  id: string;
  name_uk: string;
  description_uk: string;
  cycles: number;
  total_duration_seconds: number;
  difficulty: 'easy' | 'medium' | 'hard';
  tags: string[];
}

/* ── API ── */

export async function getBreathingExercises(): Promise<BreathingExerciseShort[]> {
  const res = await client.get<BreathingExerciseShort[]>('/breathing-exercises/');
  return res.data;
}

export async function getBreathingExercise(id: string): Promise<BreathingExercise> {
  const res = await client.get<BreathingExercise>(`/breathing-exercises/${id}`);
  return res.data;
}

