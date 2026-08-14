import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Workspace from '../src/components/workspace/Workspace';
import { baseRoutes, installFetchMock, whatIfResult } from './fixtures';

describe('what-if workspace', () => {
  it('runs a temporary what-if analysis without persisting anything', async () => {
    const user = userEvent.setup();
    const fetchMock = installFetchMock({
      ...baseRoutes(),
      'POST /grids/sample/what-if': (init) => {
        const body = JSON.parse(String(init?.body));
        expect(body.solar_output_mw).toBe(100);
        return { status: 200, body: whatIfResult };
      },
    });

    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B1')).toBeInTheDocument());

    const slider = screen.getByLabelText(/solar output/i);
    fireEvent.change(slider, { target: { value: '100' } });

    await screen.findByText('TEMPORARY');
    await screen.findByText('Renewable: 100 MW');

    const putCalls = fetchMock.mock.calls.filter(
      ([input, init]) => String(input).includes('/grids/sample') && init?.method === 'PUT',
    );
    expect(putCalls).toHaveLength(0);

    await user.click(screen.getByRole('button', { name: /^clear$/i }));
    await waitFor(() =>
      expect(screen.queryByText('TEMPORARY')).not.toBeInTheDocument(),
    );
  });

  it('sends the what-if overrides together in one request', async () => {
    const fetchMock = installFetchMock({
      ...baseRoutes(),
      'POST /grids/sample/what-if': () => ({ status: 200, body: whatIfResult }),
    });

    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B1')).toBeInTheDocument());

    fireEvent.change(screen.getByLabelText(/wind output/i), { target: { value: '60' } });
    fireEvent.change(screen.getByLabelText(/load scale/i), { target: { value: '1.2' } });

    await screen.findByText('TEMPORARY');
    await waitFor(() => {
      const calls = fetchMock.mock.calls.filter(([input]) =>
        String(input).includes('/what-if'),
      );
      expect(calls.length).toBeGreaterThan(0);
      const last = calls[calls.length - 1];
      const body = JSON.parse(String(last[1]?.body));
      expect(body.wind_output_mw).toBe(60);
      expect(body.load_scale).toBeCloseTo(1.2);
      expect(body.solar_output_mw).toBeUndefined();
    });
  });
});
