import client from './client';
import type {
  AdminUserListResponse,
  BlockUserRequest,
  BlockUserResponse,
  SystemStats,
  SystemHealth,
} from '../types';

const BASE = '/admin';

/* ── Користувачі ── */

export interface GetUsersParams {
  page?: number;
  per_page?: number;
  search?: string;
  role?: 'user' | 'admin';
  is_blocked?: boolean;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

/** Список користувачів з пагінацією */
export async function getUsers(params: GetUsersParams = {}): Promise<AdminUserListResponse> {
  const res = await client.get<AdminUserListResponse>(`${BASE}/users`, { params });
  return res.data;
}

/** Заблокувати / розблокувати користувача */
export async function blockUser(
  userId: string,
  data: BlockUserRequest,
): Promise<BlockUserResponse> {
  const res = await client.patch<BlockUserResponse>(`${BASE}/users/${userId}/block`, data);
  return res.data;
}

/* ── Статистика ── */

/** Загальна статистика системи */
export async function getSystemStats(): Promise<SystemStats> {
  const res = await client.get<SystemStats>(`${BASE}/stats`);
  return res.data;
}

/* ── Здоров'я ── */

/** Моніторинг здоров'я системи */
export async function getSystemHealth(): Promise<SystemHealth> {
  const res = await client.get<SystemHealth>(`${BASE}/health`);
  return res.data;
}

/* ── База знань (RAG) ── */

export interface KnowledgeDocument {
  id: string;
  title: string;
  category: string;
  source: string | null;
  status: 'active' | 'processing' | 'archived' | 'error';
  chunk_count: number | null;
  created_at: string;
}

export interface KnowledgeDocumentListResponse {
  documents: KnowledgeDocument[];
  total: number;
}

export interface KnowledgeUploadResponse {
  id: string;
  title: string;
  status: string;
  message: string;
}

/** Список документів бази знань */
export async function getKnowledgeDocuments(
  params: { limit?: number; offset?: number } = {},
): Promise<KnowledgeDocumentListResponse> {
  const res = await client.get<KnowledgeDocumentListResponse>(`${BASE}/knowledge`, { params });
  return res.data;
}

/** Завантажити документ */
export async function uploadKnowledgeDocument(
  file: File,
  title: string,
  category: string = 'other',
  source?: string,
  onUploadProgress?: (percent: number) => void,
): Promise<KnowledgeUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);
  formData.append('category', category);
  if (source) formData.append('source', source);

  const res = await client.post<KnowledgeUploadResponse>(`${BASE}/knowledge`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onUploadProgress
      ? (e) => {
          const percent = e.total ? Math.round((e.loaded * 100) / e.total) : 0;
          onUploadProgress(percent);
        }
      : undefined,
  });
  return res.data;
}

/** Видалити документ */
export async function deleteKnowledgeDocument(docId: string): Promise<void> {
  await client.delete(`${BASE}/knowledge/${docId}`);
}

/** Переобробити документ (re-embed) */
export async function reprocessKnowledgeDocument(
  docId: string,
): Promise<KnowledgeUploadResponse> {
  const res = await client.post<KnowledgeUploadResponse>(
    `${BASE}/knowledge/${docId}/reprocess`,
  );
  return res.data;
}
