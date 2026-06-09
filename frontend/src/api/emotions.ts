import client from './client';
import type {
  EmotionEntry,
  EmotionEntryCreate,
  EmotionEntryUpdate,
  EmotionGenerateRequest,
  EmotionGenerateResponse,
} from '../types';

const BASE = '/emotions';

/** Створити запис у щоденнику */
export async function createEmotionEntry(data: EmotionEntryCreate): Promise<EmotionEntry> {
  const res = await client.post<EmotionEntry>(BASE + '/', data);
  return res.data;
}

/** Отримати записи за місяць */
export async function getEntriesByMonth(
  month: number,
  year: number,
): Promise<EmotionEntry[]> {
  const res = await client.get<EmotionEntry[]>(BASE + '/', {
    params: { month, year },
  });
  return res.data;
}

/** Отримати запис за конкретну дату */
export async function getEntryByDate(date: string): Promise<EmotionEntry> {
  const res = await client.get<EmotionEntry>(`${BASE}/date/${date}`);
  return res.data;
}

/** Оновити запис */
export async function updateEmotionEntry(
  id: string,
  data: EmotionEntryUpdate,
): Promise<EmotionEntry> {
  const res = await client.patch<EmotionEntry>(`${BASE}/${id}`, data);
  return res.data;
}

/** Видалити запис */
export async function deleteEmotionEntry(id: string): Promise<void> {
  await client.delete(`${BASE}/${id}`);
}

/** Згенерувати опис стану AI */
export async function generateEmotionSummary(
  data: EmotionGenerateRequest,
): Promise<EmotionGenerateResponse> {
  const res = await client.post<EmotionGenerateResponse>(BASE + '/generate', data);
  return res.data;
}

