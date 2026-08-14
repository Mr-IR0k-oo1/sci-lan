import type { ApiErrorDetail } from '../types';

export const API_BASE = '/api/v1';

export class ApiRequestError extends Error {
  readonly status: number;
  readonly detail: ApiErrorDetail;

  constructor(status: number, detail: ApiErrorDetail) {
    super(detail.message);
    this.name = 'ApiRequestError';
    this.status = status;
    this.detail = detail;
  }
}

export function isApiRequestError(error: unknown): error is ApiRequestError {
  return error instanceof ApiRequestError;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiRequestError(0, {
      code: 'network_error',
      message: 'Could not reach the GridFlex backend. Is the server running?',
    });
  }

  if (!response.ok) {
    let detail: ApiErrorDetail = {
      code: 'http_error',
      message: `Request failed with status ${response.status}.`,
    };
    try {
      const body = (await response.json()) as { detail?: ApiErrorDetail };
      if (body.detail) detail = body.detail;
    } catch {
      // keep the default detail
    }
    throw new ApiRequestError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const get = <T>(path: string): Promise<T> => request<T>(path);
export const post = <T>(path: string, body: unknown): Promise<T> =>
  request<T>(path, { method: 'POST', body: JSON.stringify(body) });
export const put = <T>(path: string, body: unknown): Promise<T> =>
  request<T>(path, { method: 'PUT', body: JSON.stringify(body) });
export const del = <T>(path: string): Promise<T> => request<T>(path, { method: 'DELETE' });

export async function download(
  path: string,
  filename: string,
  init?: RequestInit,
): Promise<void> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    let detail: ApiErrorDetail = {
      code: 'http_error',
      message: `Request failed with status ${response.status}.`,
    };
    try {
      const body = (await response.json()) as { detail?: ApiErrorDetail };
      if (body.detail) detail = body.detail;
    } catch {
      // keep the default detail
    }
    throw new ApiRequestError(response.status, detail);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
