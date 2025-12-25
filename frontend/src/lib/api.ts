import { API_ENDPOINTS } from './constants';
import { getAuthToken, useAuthStore } from '@/stores/authStore';

const API_BASE = '';

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

/**
 * Make authenticated API requests
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  requiresAuth: boolean = true
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  // Add auth header if required and token exists
  if (requiresAuth) {
    const token = getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle 401 Unauthorized - logout and redirect to login
  if (response.status === 401) {
    useAuthStore.getState().logout();
    window.location.href = '/login';
    throw new ApiError('Session expired. Please login again.', 401);
  }

  // Handle rate limiting
  if (response.status === 429) {
    const error = await response.json().catch(() => ({ detail: 'Rate limit exceeded' }));
    throw new ApiError(error.detail || 'Too many requests. Please try again later.', 429);
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new ApiError(error.detail || error.message || 'Request failed', response.status);
  }

  return response.json();
}

// Auth API (no auth required for these)
export const authApi = {
  getStatus: () => request<{
    is_setup_complete: boolean;
    is_authenticated: boolean;
  }>(`${API_ENDPOINTS.AUTH}/status`, {}, false),

  setup: (username: string, password: string) => request<{
    access_token: string;
    token_type: string;
    expires_in: number;
  }>(`${API_ENDPOINTS.AUTH}/setup`, {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  }, false),

  login: (username: string, password: string) => request<{
    access_token: string;
    token_type: string;
    expires_in: number;
  }>(`${API_ENDPOINTS.AUTH}/login`, {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  }, false),

  logout: () => request<{ status: string; message: string }>(
    `${API_ENDPOINTS.AUTH}/logout`,
    { method: 'POST' }
  ),

  verify: () => request<{ status: string; message: string }>(
    `${API_ENDPOINTS.AUTH}/verify`
  ),

  getProfile: () => request<{
    username: string;
    created_at: string;
  }>(`${API_ENDPOINTS.AUTH}/profile`),

  changePassword: (currentPassword: string, newPassword: string) => request<{
    status: string;
    message: string;
  }>(`${API_ENDPOINTS.AUTH}/change-password`, {
    method: 'POST',
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  }),
};

// Settings API
export const settingsApi = {
  get: () => request<{
    openalgo_host: string;
    openalgo_ws_url: string;
    is_configured: boolean;
    has_api_key: boolean;
  }>(API_ENDPOINTS.SETTINGS),

  update: (data: {
    openalgo_api_key?: string;
    openalgo_host?: string;
    openalgo_ws_url?: string;
  }) => request<{ status: string; message: string }>(API_ENDPOINTS.SETTINGS, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),

  test: () => request<{
    success: boolean;
    message: string;
    data?: Record<string, unknown>;
  }>(API_ENDPOINTS.SETTINGS_TEST, {
    method: 'POST',
  }),
};

// Workflows API
export interface Workflow {
  id: number;
  name: string;
  description: string | null;
  nodes: Node[];
  edges: Edge[];
  is_active: boolean;
  schedule_job_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkflowListItem {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_execution_status: string | null;
}

export interface Node {
  id: string;
  type?: string;
  position: { x: number; y: number };
  data: Record<string, unknown>;
  [key: string]: unknown;
}

export interface Edge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string | null;
  targetHandle?: string | null;
  [key: string]: unknown;
}

export interface WorkflowExecution {
  id: number;
  workflow_id: number;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  logs: { time: string; message: string; level: string }[];
  error: string | null;
}

export interface WorkflowExportData {
  version: string;
  name: string;
  description: string | null;
  nodes: Node[];
  edges: Edge[];
  exported_at: string;
}

export const workflowsApi = {
  list: () => request<WorkflowListItem[]>(API_ENDPOINTS.WORKFLOWS),

  get: (id: number) => request<Workflow>(`${API_ENDPOINTS.WORKFLOWS}/${id}`),

  create: (data: {
    name: string;
    description?: string;
    nodes?: Node[];
    edges?: Edge[];
  }) => request<Workflow>(API_ENDPOINTS.WORKFLOWS, {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  update: (id: number, data: {
    name?: string;
    description?: string;
    nodes?: Node[];
    edges?: Edge[];
  }) => request<Workflow>(`${API_ENDPOINTS.WORKFLOWS}/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),

  delete: (id: number) => request<{ status: string; message: string }>(
    `${API_ENDPOINTS.WORKFLOWS}/${id}`,
    { method: 'DELETE' }
  ),

  activate: (id: number) => request<{
    status: string;
    message: string;
    job_id?: string;
    next_run?: string;
  }>(`${API_ENDPOINTS.WORKFLOWS}/${id}/activate`, {
    method: 'POST',
  }),

  deactivate: (id: number) => request<{ status: string; message: string }>(
    `${API_ENDPOINTS.WORKFLOWS}/${id}/deactivate`,
    { method: 'POST' }
  ),

  execute: (id: number) => request<{
    status: string;
    message: string;
    execution_id?: number;
    logs?: { time: string; message: string; level: string }[];
  }>(`${API_ENDPOINTS.WORKFLOWS}/${id}/execute`, {
    method: 'POST',
  }),

  getExecutions: (id: number, limit = 20) => request<WorkflowExecution[]>(
    `${API_ENDPOINTS.WORKFLOWS}/${id}/executions?limit=${limit}`
  ),

  // Export workflow for sharing
  export: (id: number) => request<WorkflowExportData>(
    `${API_ENDPOINTS.WORKFLOWS}/${id}/export`
  ),

  // Import workflow from JSON
  import: (data: WorkflowExportData) => request<Workflow>(
    `${API_ENDPOINTS.WORKFLOWS}/import`,
    {
      method: 'POST',
      body: JSON.stringify(data),
    }
  ),
};

// Symbols API
export const symbolsApi = {
  search: (query: string, exchange = 'NSE') => request<{
    status: string;
    data: Array<{
      symbol: string;
      name: string;
      exchange: string;
      lotsize: number;
      tick_size: number;
    }>;
    message?: string;
  }>(`${API_ENDPOINTS.SYMBOLS_SEARCH}?query=${encodeURIComponent(query)}&exchange=${exchange}`),

  quotes: (symbol: string, exchange = 'NSE') => request<{
    status: string;
    data: {
      ltp: number;
      open: number;
      high: number;
      low: number;
      prev_close: number;
      volume: number;
      bid: number;
      ask: number;
    };
  }>(`${API_ENDPOINTS.SYMBOLS_QUOTES}?symbol=${encodeURIComponent(symbol)}&exchange=${exchange}`),
};
