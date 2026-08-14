import { isApiRequestError } from '../api/client';

export function describeError(error: unknown): string {
  if (isApiRequestError(error)) {
    const detail = error.detail;
    if (detail.code === 'power_flow_not_converged') {
      const iterations = detail.iterations;
      const suffix = iterations != null ? ` after ${iterations} iterations` : '';
      return `Power flow did not converge${suffix}. Check the grid for isolated buses or extreme values.`;
    }
    return detail.message || `Request failed (${error.status}).`;
  }
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred.';
}
