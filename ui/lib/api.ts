// API client for communicating with the NestJS backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001/api';

// Token management
const TOKEN_KEY = 'qdesign_token';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
}

// API Error class
export class ApiError extends Error {
  constructor(
    public statusCode: number,
    message: string,
    public data?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Generic fetch wrapper
async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });
  
  const data = await response.json().catch(() => ({}));
  
  if (!response.ok) {
    throw new ApiError(
      response.status,
      data.message || 'An error occurred',
      data,
    );
  }
  
  return data as T;
}

// Auth API
export const authApi = {
  register: (body: { name: string; email: string; password: string }) =>
    request<{ user: { id: string; name: string; email: string; avatar?: string }; token: string }>(
      '/auth/register',
      { method: 'POST', body: JSON.stringify(body) },
    ),
    
  login: (body: { email: string; password: string }) =>
    request<{ user: { id: string; name: string; email: string; avatar?: string }; token: string }>(
      '/auth/login',
      { method: 'POST', body: JSON.stringify(body) },
    ),
    
  getSession: () =>
    request<{ user: { id: string; name: string; email: string; avatar?: string } }>(
      '/auth/session',
    ),
    
  logout: () =>
    request<{ success: boolean }>('/auth/logout', { method: 'POST' }),
};

// Projects API
export const projectsApi = {
  list: () =>
    request<{ projects: any[] }>('/projects'),
    
  get: (id: string) =>
    request<{ project: any }>(`/projects/${id}`),
    
  create: (body: { name: string; mainObjective: string; secondaryObjectives?: string[]; description?: string }) =>
    request<{ project: any }>('/projects', { method: 'POST', body: JSON.stringify(body) }),
    
  update: (id: string, body: Partial<any>) =>
    request<{ project: any }>(`/projects/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
    
  delete: (id: string) =>
    request<void>(`/projects/${id}`, { method: 'DELETE' }),
    
  join: (hash: string) =>
    request<{ project: any; message: string }>('/projects/join', { method: 'POST', body: JSON.stringify({ hash }) }),
    
  createCheckpoint: (id: string, body: { name: string; description?: string }) =>
    request<{ checkpoint: any; project: any }>(`/projects/${id}/checkpoints`, { method: 'POST', body: JSON.stringify(body) }),
    
  restoreCheckpoint: (projectId: string, checkpointId: string) =>
    request<{ project: any; message: string }>(`/projects/${projectId}/checkpoints/${checkpointId}/restore`, { method: 'POST' }),
};
