/** User Management API — 用户注册/登录与信息管理
 *
 * 对应功能模块：用户管理（注册/登录、信息管理、权限控制）
 */

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface UserAccount {
  user_id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'user' | 'admin';
  created_at: string;
}

export interface UserPreferences {
  career_goals: string[];
  preferred_industries: string[];
  preferred_locations: string[];
  salary_expectation: [number, number] | null;
  privacy_level: 'none' | 'basic' | 'full';
}

export interface UserProfile extends UserAccount, UserPreferences {
  skills: string[];
  experience_years: number;
  education_level: string;
}

/** 获取当前登录用户信息 */
export async function getCurrentUser(): Promise<UserProfile> {
  const res = await fetch(`${BASE}/users/me`, { credentials: 'include' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/** 更新用户基本信息与职业偏好 */
export async function updateUserProfile(
  userId: string,
  profile: Partial<UserProfile>
): Promise<UserProfile> {
  const res = await fetch(`${BASE}/users/${encodeURIComponent(userId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/** 用户登录 */
export async function loginUser(params: {
  email: string;
  password: string;
}): Promise<{ token: string; user: UserProfile }> {
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/** 用户注册 */
export async function registerUser(params: {
  email: string;
  password: string;
  name: string;
}): Promise<{ token: string; user: UserProfile }> {
  const res = await fetch(`${BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
