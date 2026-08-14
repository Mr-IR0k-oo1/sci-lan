import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiRequestError, isApiRequestError, post } from '../src/api/client';
import { describeError } from '../src/lib/errors';

function jsonResponse(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('api client error handling', () => {
  it('throws a typed network error when fetch fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    const promise = post('/grids', { name: 'x' });
    await expect(promise).rejects.toBeInstanceOf(ApiRequestError);
    await promise.catch((error: unknown) => {
      expect(isApiRequestError(error)).toBe(true);
      if (isApiRequestError(error)) {
        expect(error.detail.code).toBe('network_error');
        expect(describeError(error)).toContain('backend');
      }
    });
  });

  it('surfaces non-convergence details from a 409', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            detail: {
              code: 'power_flow_not_converged',
              message: 'Power flow did not converge.',
              iterations: 50,
            },
          },
          409,
        ),
      ),
    );
    try {
      await post('/grids/sample/analyze/power-flow', {});
      expect.unreachable();
    } catch (error) {
      expect(describeError(error)).toContain('did not converge after 50 iterations');
    }
  });

  it('falls back to the HTTP status message for non-JSON errors', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('Internal Server Error', { status: 500 })),
    );
    try {
      await post('/grids/sample/analyze/power-flow', {});
      expect.unreachable();
    } catch (error) {
      expect(isApiRequestError(error)).toBe(true);
      if (isApiRequestError(error)) {
        expect(error.status).toBe(500);
        expect(error.detail.code).toBe('http_error');
      }
    }
  });

  it('uses the backend message when one is provided', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(
          { detail: { code: 'grid_not_found', message: 'Grid not found.' } },
          404,
        ),
      ),
    );
    try {
      await post('/grids/nope', {});
      expect.unreachable();
    } catch (error) {
      expect(describeError(error)).toBe('Grid not found.');
    }
  });
});
