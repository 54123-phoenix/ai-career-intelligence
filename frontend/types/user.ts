/** User Domain Types — 用户管理与权限控制 */

export interface UserAccount {
  user_id: string;
  email: string;
  name: string;
  avatar?: string;
  role: "user" | "admin";
  created_at: string;
}

export interface UserPreferences {
  career_goals: string[];
  preferred_industries: string[];
  preferred_locations: string[];
  salary_expectation: [number, number] | null;
  privacy_level: "none" | "basic" | "full";
}

export interface UserProfile extends UserAccount, UserPreferences {
  skills: string[];
  experience_years: number;
  education_level: string;
}

export interface UserSession {
  session_id: string;
  user_id: string;
  login_at: string;
  expires_at: string;
}

export interface AuthResponse {
  token: string;
  user: UserProfile;
}
