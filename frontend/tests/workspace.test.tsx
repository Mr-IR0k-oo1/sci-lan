import { describe, expect, it } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Workspace from '../src/components/workspace/Workspace';
import {
  baseRoutes,
  installFetchMock,
  sampleGrid,
  sampleResult,
} from './fixtures';

describe('workspace', () => {
  it('loads the sample grid and renders buses on the canvas', async () => {
    installFetchMock(baseRoutes());
    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B1')).toBeInTheDocument());
    expect(screen.getByTestId('bus-B4')).toBeInTheDocument();
    expect(screen.getByText('5-bus sample')).toBeInTheDocument();
    expect(screen.getByTestId('line-L1')).toBeInTheDocument();
  });

  it('runs a power flow analysis and shows the impact score', async () => {
    const user = userEvent.setup();
    installFetchMock({
      ...baseRoutes(),
      'POST /grids/sample/analyze/power-flow': () => ({ status: 200, body: sampleResult }),
    });
    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B1')).toBeInTheDocument());

    await user.click(screen.getByRole('button', { name: /run analysis/i }));
    await screen.findByText('96.7');
    expect(screen.getByText('Grade A')).toBeInTheDocument();
  });

  it('shows an actionable message when power flow does not converge', async () => {
    const user = userEvent.setup();
    installFetchMock({
      ...baseRoutes(),
      'POST /grids/sample/analyze/power-flow': () => ({
        status: 409,
        body: {
          detail: {
            code: 'power_flow_not_converged',
            message: 'Power flow did not converge.',
            iterations: 50,
          },
        },
      }),
    });
    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B1')).toBeInTheDocument());

    await user.click(screen.getByRole('button', { name: /run analysis/i }));
    await screen.findByRole('alert');
    expect(screen.getByRole('alert')).toHaveTextContent(/did not converge after 50 iterations/i);
  });

  it('stops before analysis and lists issues when validation fails', async () => {
    const user = userEvent.setup();
    installFetchMock({
      ...baseRoutes(),
      'POST /grids/sample/validate': () => ({
        status: 200,
        body: {
          valid: false,
          errors: [{ code: 'no_slack', message: "Line 'L1' has zero reactance.", location: 'lines' }],
        },
      }),
    });
    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B1')).toBeInTheDocument());

    await user.click(screen.getByRole('button', { name: /run analysis/i }));
    await screen.findByText(/zero reactance/i);
  });

  it('edits a bus property and saves the grid to the backend', async () => {
    const user = userEvent.setup();
    const fetchMock = installFetchMock({
      ...baseRoutes(),
      'PUT /grids/sample': () => ({ status: 200, body: sampleGrid }),
    });
    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B2')).toBeInTheDocument());

    await user.click(screen.getByTestId('bus-B2'));
    await screen.findByText('Bus B2');

    const input = screen.getByLabelText('Voltage magnitude (pu)');
    await user.clear(input);
    await user.type(input, '1.05');
    await user.tab();

    await user.click(screen.getByRole('button', { name: /save grid/i }));
    await waitFor(() => {
      const putCalls = fetchMock.mock.calls.filter(
        ([input, init]) => String(input).endsWith('/grids/sample') && init?.method === 'PUT',
      );
      expect(putCalls).toHaveLength(1);
    });
  });

  it('rejects an invalid number in a property field without applying it', async () => {
    const user = userEvent.setup();
    const fetchMock = installFetchMock({
      ...baseRoutes(),
      'PUT /grids/sample': () => ({ status: 200, body: sampleGrid }),
    });
    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B2')).toBeInTheDocument());

    await user.click(screen.getByTestId('bus-B2'));
    await screen.findByText('Bus B2');

    const input = screen.getByLabelText('Voltage magnitude (pu)');
    await user.clear(input);
    await user.type(input, 'abc');
    await user.tab();

    await screen.findByText(/enter a valid number/i);
    await user.click(screen.getByRole('button', { name: /save grid/i }));

    const putCalls = fetchMock.mock.calls.filter(
      ([url, init]) => String(url).endsWith('/grids/sample') && init?.method === 'PUT',
    );
    expect(putCalls).toHaveLength(1);
    const sent = JSON.parse(String(putCalls[0][1]?.body));
    const b2 = sent.buses.find((bus: { id: string }) => bus.id === 'B2');
    expect(b2.voltage_magnitude).toBe(1.04);
  });
});
