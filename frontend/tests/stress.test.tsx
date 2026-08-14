import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import Workspace from '../src/components/workspace/Workspace';
import {
  baseRoutes,
  installFetchMock,
  mitigationTestResult,
  stressedAnalysis,
} from './fixtures';

describe('stress analysis workspace', () => {
  it('shows an empty state before running a stress analysis', async () => {
    installFetchMock({
      ...baseRoutes(),
    });

    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B1')).toBeInTheDocument());

    expect(screen.getByTestId('stress-results')).toBeInTheDocument();
    expect(
      screen.getByText(/run a stress analysis to see grid health/i),
    ).toBeInTheDocument();
  });

  it('runs a stress analysis and shows grid health, issues, and recommendations', async () => {
    const fetchMock = installFetchMock({
      ...baseRoutes(),
      'POST /grids/sample/stress': () => ({ status: 200, body: stressedAnalysis }),
    });

    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B1')).toBeInTheDocument());

    const stressButton = screen.getByRole('button', { name: /^stress$/i });
    fireEvent.click(stressButton);

    await screen.findByText('62.5');
    await screen.findByText('MODERATE');
    expect(screen.getByText(/stress score is moderate/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /^issues \(3\)$/i }));
    await screen.findByText('Bus undervoltage');
    expect(screen.getByText('Transmission line overloaded')).toBeInTheDocument();
    expect(screen.getByText('Generation may be insufficient')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /^recommendations$/i }));
    await screen.findByText('Add shunt compensation to support voltage');
    expect(screen.getByText('Reduce load on overloaded transmission lines')).toBeInTheDocument();
    expect(screen.getAllByText(/high priority/i).length).toBe(2);

    const stressCalls = fetchMock.mock.calls.filter(([input]) =>
      String(input).includes('/stress'),
    );
    expect(stressCalls.length).toBeGreaterThan(0);
  });

  it('reports an error when the stress analysis fails', async () => {
    installFetchMock({
      ...baseRoutes(),
      'POST /grids/sample/stress': () => ({
        status: 422,
        body: { detail: { code: 'invalid_grid', message: 'Grid is invalid.' } },
      }),
    });

    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B1')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /^stress$/i }));
    await screen.findAllByText(/grid is invalid/i);
  });

  it('locates an issue component from the issue explorer', async () => {
    installFetchMock({
      ...baseRoutes(),
      'POST /grids/sample/stress': () => ({ status: 200, body: stressedAnalysis }),
    });

    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B1')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /^stress$/i }));
    await screen.findByText('62.5');

    fireEvent.click(screen.getByRole('button', { name: /^issues \(3\)$/i }));
    const locate = await screen.findAllByRole('button', { name: /^locate$/i });
    expect(locate.length).toBeGreaterThan(0);
  });
});

describe('mitigation comparison', () => {
  it('runs all mitigation tests and shows before/after scores', async () => {
    const fetchMock = installFetchMock({
      ...baseRoutes(),
      'POST /grids/sample/stress': () => ({ status: 200, body: stressedAnalysis }),
      'POST /analyses/analysis-2/mitigation-tests': (init) => {
        const body = JSON.parse(String(init?.body));
        if (body.mitigation_id === 'mitigation_001') {
          return { status: 200, body: [mitigationTestResult] };
        }
        return { status: 200, body: [] };
      },
    });

    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B1')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /^stress$/i }));
    await screen.findByText('62.5');

    fireEvent.click(screen.getByRole('button', { name: /^mitigations$/i }));
    fireEvent.click(screen.getByRole('button', { name: /^test all \(1\)$/i }));

    await screen.findByText('38.2');
    const tests = fetchMock.mock.calls.filter(([input]) =>
      String(input).includes('/mitigation-tests'),
    );
    expect(tests.length).toBeGreaterThan(0);
    const body = JSON.parse(String(tests[0][1]?.body));
    expect(body.mitigation_id).toBe('mitigation_001');
    expect(body.run_all).toBe(false);
  });

  it('renders a hint when there are no mitigation candidates', async () => {
    const noCandidates = {
      ...stressedAnalysis,
      mitigation_candidates: [],
    };
    installFetchMock({
      ...baseRoutes(),
      'POST /grids/sample/stress': () => ({ status: 200, body: noCandidates }),
    });

    render(<Workspace />);
    await waitFor(() => expect(screen.getByTestId('bus-B1')).toBeInTheDocument());

    fireEvent.click(screen.getByRole('button', { name: /^stress$/i }));
    await screen.findByText('62.5');

    fireEvent.click(screen.getByRole('button', { name: /^mitigations$/i }));
    await screen.findByText(/no mitigation candidates/i);
  });
});
