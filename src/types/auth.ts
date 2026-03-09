// Auth types for BioLink

export interface AuthUser {
  username: string;
  email: string | null;
  full_name: string | null;
  role: string; // 'admin' | 'researcher' | 'viewer'
  scopes: string[];
  disabled: boolean;
  created_at?: string | null;
  last_login?: string | null;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export type UserRole = 'admin' | 'researcher' | 'viewer';

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface UpdateProfileRequest {
  full_name?: string;
  email?: string;
}

export interface AdminUpdateUserRequest {
  role?: string;
  scopes?: string[];
  disabled?: boolean;
  full_name?: string;
  email?: string;
}
