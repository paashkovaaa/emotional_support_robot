import client from './client';
import type {
  LoginRequest,
  RegisterRequest,
  RegisterResponse,
  TokenResponse,
  User,
  Profile,
  ProfileUpdate,
  SurveyRequest,
} from '../types';

/* ── Auth ── */

export async function register(data: RegisterRequest): Promise<RegisterResponse> {
  const res = await client.post<RegisterResponse>('/auth/register', data);
  return res.data;
}

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const res = await client.post<TokenResponse>('/auth/login', data);
  return res.data;
}

export async function refreshTokens(refreshToken: string): Promise<TokenResponse> {
  const res = await client.post<TokenResponse>('/auth/refresh', {
    refresh_token: refreshToken,
  });
  return res.data;
}

export async function logout(): Promise<void> {
  await client.post('/auth/logout');
}

export async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  await client.post('/auth/change-password', {
    old_password: oldPassword,
    new_password: newPassword,
  });
}

/* ── User / Profile ── */

export async function getCurrentUser(): Promise<User> {
  const res = await client.get<User>('/profile/me');
  return res.data;
}

export async function getProfile(): Promise<Profile> {
  const res = await client.get<Profile>('/profile/');
  return res.data;
}

export async function completeSurvey(data: SurveyRequest): Promise<Profile> {
  const res = await client.post<Profile>('/profile/survey', data);
  return res.data;
}

export async function updateProfile(data: ProfileUpdate): Promise<Profile> {
  const res = await client.patch<Profile>('/profile/', data);
  return res.data;
}

export async function deleteAccount(): Promise<void> {
  await client.delete('/profile/');
}

