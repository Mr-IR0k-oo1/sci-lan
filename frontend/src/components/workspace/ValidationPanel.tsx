import type { ComponentSelection, GridModel, ValidationIssue } from '../../types';
import { issueTarget } from '../../lib/issues';
import { Button, Section } from '../ui';
import { ErrorIcon } from '../icons';

interface ValidationPanelProps {
  grid: GridModel | null;
  issues: ValidationIssue[];
  onSelect: (selection: ComponentSelection | null) => void;
}

export function ValidationPanel({ grid, issues, onSelect }: ValidationPanelProps) {
  if (!grid) {
    return (
      <Section title="Validation">
        <p className="panel-hint">Load a grid to run validation.</p>
      </Section>
    );
  }
  return (
    <Section
      title="Validation"
      action={
        issues.length > 0 ? (
          <span className="status-badge status-bad">{issues.length}</span>
        ) : null
      }
    >
      {issues.length === 0 ? (
        <p className="panel-hint">
          No issues. Grid is ready for a power flow analysis.
        </p>
      ) : (
        <ul className="validation-issues">
          {issues.map((issue, index) => {
            const target = issueTarget(issue, grid);
            return (
              <li key={`${issue.code}-${index}`}>
                <button
                  type="button"
                  className="issue-row"
                  disabled={!target}
                  onClick={() => target && onSelect(target)}
                >
                  <span className="issue-icon" aria-hidden="true">
                    <ErrorIcon />
                  </span>
                  <span>{issue.message}</span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
      {issues.length > 0 ? (
        <Button variant="ghost" className="link-button" onClick={() => onSelect(null)}>
          Clear selection
        </Button>
      ) : null}
    </Section>
  );
}
