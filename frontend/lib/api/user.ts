/** User Management API — 用户注册/登录与信息管理 */

import { apiFetch } from './client';
import type { UserProfile, AuthResponse } from '@/types/user';

export async function loginUser(params: {
  email: string;
  password: string;
}): Promise<AuthResponse> {
  return apiFetch<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function registerUser(params: {
  email: string;
  password: string;
  name: string;
}): Promise<AuthResponse> {
  return apiFetch<AuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getCurrentUser(): Promise<UserProfile> {
  return apiFetch<UserProfile>('/users/me');
}

export async function updateUserProfile(profile: Partial<UserProfile>): Promise<UserProfile> {
  return apiFetch<UserProfile>('/users/me', {
    method: 'PATCH',
    body: JSON.stringify(profile),
  });
}

export async function getUserHistory(params?: { page?: number; limit?: number }): Promise<{
  items: UserHistoryItem[];
  total: number;
}> {
  const search = new URLSearchParams();
  if (params?.page) search.set('page', String(params.page));
  if (params?.limit) search.set('limit', String(params.limit));
  return apiFetch(`/users/me/history?${search.toString()}`);
}

export interface UserHistoryItem {
  id: string;
  type: 'analysis' | 'simulation' | 'chat' | 'profile_update';
  title: string;
  description: string;
  created_at: string;
}
