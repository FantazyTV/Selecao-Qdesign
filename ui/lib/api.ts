// API client for communicating with the NestJS backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001/api';
const SEARCH_API_URL = process.env.NEXT_PUBLIC_SEARCH_API_URL || 'http://localhost:8000';

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

// Search API (FastAPI)
async function searchRequest<T>(endpoint: string, body: unknown): Promise<T> {
  const response = await fetch(`${SEARCH_API_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiError(response.status, data.detail || 'Search error', data);
  }
  return data as T;
}

export const searchApi = {
  hybrid: (body: {
    pdb_id?: string;
    sequence?: string;
    text_query?: string;
    top_k?: number;
    alpha?: number;
    beta?: number;
    gamma?: number;
    use_structure?: boolean;
    include_mutations?: boolean;
  }) => searchRequest<{ results: any[]; mutations?: any[] }>('/search_hybrid', body),
};

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
    
  create: (body: { name: string; mainObjective: string; secondaryObjectives?: string[]; constraints?: string[]; notes?: string[]; description?: string }) =>
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
    
  addComment: (projectId: string, itemId: string, comment: string) =>
    request<{ project: any }>(`/projects/${projectId}/data-pool/${itemId}/comments`, { 
      method: 'POST', 
      body: JSON.stringify({ text: comment }) 
    }),
    
  deleteComment: (projectId: string, itemId: string, commentId: string) =>
    request<{ project: any }>(`/projects/${projectId}/data-pool/${itemId}/comments/${commentId}`, { 
      method: 'DELETE' 
    }),
};

// Combined API object
export const api = {
  auth: authApi,
  projects: projectsApi,
};
