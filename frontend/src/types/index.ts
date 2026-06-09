/* ── Emotion Diary ── */

export interface EmotionEntry {
  id: string;
  user_id: string;
  entry_date: string; // "YYYY-MM-DD"
  emoji: string | null;
  user_description: string | null;
  bot_description: string | null;
  emotion_tags: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface EmotionEntryCreate {
  entry_date: string;
  emoji?: string | null;
  user_description?: string | null;
  bot_description?: string | null;
  emotion_tags?: string[] | null;
}

export interface EmotionEntryUpdate {
  emoji?: string | null;
  user_description?: string | null;
  bot_description?: string | null;
  emotion_tags?: string[] | null;
}

export interface EmotionGenerateRequest {
  conversation_id: string;
  entry_date?: string | null;
}

export interface EmotionGenerateResponse {
  description: string;
  emoji: string;
  tags: string[];
}

/* ── Auth ── */

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  nickname: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterResponse {
  id: string;
  email: string;
  message: string;
}

export interface User {
  id: string;
  email: string | null;
  role: 'user' | 'admin';
  is_active: boolean;
  is_blocked: boolean;
  last_login: string | null;
  created_at: string;
}

/* ── Profile ── */

export type CommunicationStyle = 'analytical' | 'friendly' | 'balanced';
export type Gender = 'male' | 'female' | 'other' | 'prefer_not_to_say';

export interface SurveyRequest {
  communication_style: CommunicationStyle;
  life_area?: string | null;
  concern?: string | null;
  works_with_psychologist: boolean;
}

export interface Profile {
  id: string;
  user_id: string;
  nickname: string;
  age: number | null;
  gender: Gender | null;
  communication_style: CommunicationStyle;
  life_area: string | null;
  concern: string | null;
  works_with_psychologist: boolean;
  survey_completed: boolean;
  created_at: string;
}

export interface ProfileUpdate {
  nickname?: string | null;
  age?: number | null;
  gender?: Gender | null;
  communication_style?: CommunicationStyle | null;
  life_area?: string | null;
  concern?: string | null;
  works_with_psychologist?: boolean | null;
}

export interface Conversation {
  id: string;
  title: string | null;
  status: 'active' | 'ended';
  started_at: string;
}

/* ── Admin ── */

export interface AdminUser {
  id: string;
  email: string | null;
  role: 'user' | 'admin';
  is_active: boolean;
  is_blocked: boolean;
  last_login: string | null;
  created_at: string;
  updated_at: string;
  conversations_count: number;
  emotion_entries_count: number;
}

export interface AdminUserListResponse {
  users: AdminUser[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface BlockUserRequest {
  is_blocked: boolean;
  reason?: string | null;
}

export interface BlockUserResponse {
  id: string;
  email: string | null;
  is_blocked: boolean;
  message: string;
}

export interface CrisisStats {
  total_crisis_messages: number;
  by_level: Record<string, number>;
}

export interface SystemStats {
  total_users: number;
  active_users: number;
  blocked_users: number;
  total_conversations: number;
  active_conversations: number;
  total_messages: number;
  total_emotion_entries: number;
  crisis: CrisisStats;
  users_registered_last_7_days: number;
  users_registered_last_30_days: number;
}

export interface ServiceHealth {
  status: 'ok' | 'error' | 'unavailable';
  latency_ms: number | null;
  detail: string | null;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  uptime_seconds: number;
  database: ServiceHealth;
  redis: ServiceHealth;
  version: string;
  environment: string;
}

/* ── API Error ── */

export interface ApiError {
  detail: string;
}

