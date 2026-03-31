/**
 * Auth API functions for BioLink
 */

import { API_BASE_URL, setTokens, clearTokens, getAccessToken } from './client';
import type {
  AuthUser,
  LoginResponse,
  RegisterRequest,
  ChangePasswordRequest,
  UpdateProfileRequest,
  AdminUpdateUserRequest,
  AdminCreateUserRequest,
} from '../types/auth';

export async function loginApi(username: string, password: string): Promise<LoginResponse> {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await fetch(`${API_BASE_URL}/api/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData.toString(),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed');
  }

  const data: LoginResponse = await response.json();
  setTokens(data.access_token, data.refresh_token);
  return data;
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const token = getAccessToken();
  if (!token) throw new Error('No access token');

  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch user');
  }

  return response.json();
}

export async function logoutApi(): Promise<void> {
  const token = getAccessToken();
  if (token) {
    await fetch(`${API_BASE_URL}/api/auth/logout`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    }).catch(() => {});
  }
  clearTokens();
}

export async function registerApi(data: RegisterRequest): Promise<AuthUser> {
  const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Registration failed');
  }

  return response.json();
}

export async function changePasswordApi(data: ChangePasswordRequest): Promise<void> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/api/auth/change-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Password change failed');
  }
}

export async function updateProfileApi(data: UpdateProfileRequest): Promise<AuthUser> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Profile update failed');
  }

  return response.json();
}

export async function listUsersApi(): Promise<AuthUser[]> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/api/auth/users`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) throw new Error('Failed to list users');
  return response.json();
}

export async function adminUpdateUserApi(username: string, data: AdminUpdateUserRequest): Promise<AuthUser> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/api/auth/users/${encodeURIComponent(username)}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'User update failed');
  }

  return response.json();
}

export async function adminDeleteUserApi(username: string): Promise<void> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/api/auth/users/${encodeURIComponent(username)}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'User deletion failed');
  }
}

export async function adminCreateUserApi(data: AdminCreateUserRequest): Promise<AuthUser> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}/api/auth/users`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'User creation failed');
  }

  return response.json();
}
