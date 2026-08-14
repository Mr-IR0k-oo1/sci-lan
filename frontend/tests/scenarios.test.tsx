import { describe, expect, it } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Workspace from '../src/components/workspace/Workspace';
import {
  baseRoutes,
  installFetchMock,
  sampleResult,
  scenarioGrid,
  scenarioResult,
} from './fixtures';

function scenarioRoutes() {
  let deleted = false;
  return {
    ...baseRoutes(),
    'POST /grids/sample/scenarios': (init?: RequestInit) => {
      const body = JSON.parse(String(init?.body));
      return {
        status: 201,
        body: { id: body.id || 's1', name: body.name, grid: body.grid },
      };
    },
    'GET /grids/sample/scenarios': () => ({
      status: 200,
      body: deleted ? [] : [{ id: 's1', name: 'Peak load' }],
    }),
    'GET /grids/sample/scenarios/s1': () => ({
      status: 200,
      body: { id: 's1', name: 'Peak load', grid: scenarioGrid },
    }),
    'POST /grids/sample/scenarios/s1/analyze': () => ({
      status: 200,
      body: scenarioResult,
    }),
    'DELETE /grids/sample/scenarios/s1': () => {
      deleted = true;
      return { status: 204 };
    },
  };
}

describe('scenario workspace', () => {
  it('creates, runs, and edits a scenario without touching the base grid', async () => {
    const user = userEvent.setup();
    const fetchMock = installFetchMock(scenarioRoutes());

    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B1')).toBeInTheDocument());

    await user.type(screen.getByLabelText('New scenario name'), 'Peak load');
    await user.click(screen.getByRole('button', { name: /^create$/i }));
    await screen.findByText('Peak load');

    await user.click(screen.getByRole('button', { name: /^run$/i }));
    await screen.findByText('✓ analyzed');
    expect(screen.getByText('94.2')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /^edit$/i }));
    await screen.findByTestId('scenario-banner');

    const putCalls = fetchMock.mock.calls.filter(
      ([input, init]) => String(input).includes('/grids/sample') && init?.method === 'PUT',
    );
    expect(putCalls).toHaveLength(0);
  });

  it('saves the scenario draft through an upsert that keeps the base grid intact', async () => {
    const user = userEvent.setup();
    const fetchMock = installFetchMock(scenarioRoutes());

    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B1')).toBeInTheDocument());

    await user.type(screen.getByLabelText('New scenario name'), 'Peak load');
    await user.click(screen.getByRole('button', { name: /^create$/i }));
    await screen.findByText('Peak load');

    await user.click(screen.getByRole('button', { name: /^edit$/i }));
    await screen.findByTestId('scenario-banner');

    await user.click(screen.getByRole('button', { name: /^save scenario$/i }));
    await waitFor(() => {
      const postCalls = fetchMock.mock.calls.filter(
        ([input, init]) =>
          String(input).endsWith('/grids/sample/scenarios') && init?.method === 'POST',
      );
      expect(postCalls.length).toBeGreaterThanOrEqual(1);
      const last = postCalls[postCalls.length - 1];
      const body = JSON.parse(String(last[1]?.body));
      expect(body.id).toBe('s1');
    });
  });

  it('deletes a scenario and clears its stored result', async () => {
    const user = userEvent.setup();
    const fetchMock = installFetchMock(scenarioRoutes());

    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B1')).toBeInTheDocument());

    await user.type(screen.getByLabelText('New scenario name'), 'Peak load');
    await user.click(screen.getByRole('button', { name: /^create$/i }));
    await screen.findByText('Peak load');

    await user.click(screen.getByRole('button', { name: /^run$/i }));
    await screen.findByText('✓ analyzed');

    await user.click(screen.getByRole('button', { name: /^delete$/i }));
    await waitFor(() => {
      const delCalls = fetchMock.mock.calls.filter(
        ([input, init]) => String(input).includes('/scenarios/s1') && init?.method === 'DELETE',
      );
      expect(delCalls).toHaveLength(1);
    });
    await waitFor(() => expect(screen.queryByText('Peak load')).not.toBeInTheDocument());
  });

  it('shows base analysis results in the compare tab after running a scenario', async () => {
    const user = userEvent.setup();
    installFetchMock({
      ...scenarioRoutes(),
      'POST /grids/sample/analyze/power-flow': () => ({ status: 200, body: sampleResult }),
    });

    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B1')).toBeInTheDocument());

    await user.type(screen.getByLabelText('New scenario name'), 'Peak load');
    await user.click(screen.getByRole('button', { name: /^create$/i }));
    await screen.findByText('Peak load');
    await user.click(screen.getByRole('button', { name: /^run$/i }));
    await screen.findByText('✓ analyzed');

    await user.click(screen.getByRole('button', { name: /^run analysis$/i }));
    await screen.findByText('96.7');

    await user.click(screen.getByRole('button', { name: /^compare$/i }));
    await user.selectOptions(screen.getByLabelText('Scenario'), 's1');

    const labels = await screen.findAllByText('Total generation');
    expect(labels.length).toBeGreaterThan(0);
    expect((await screen.findAllByText('Renewable generation')).length).toBeGreaterThan(0);
  });
});
