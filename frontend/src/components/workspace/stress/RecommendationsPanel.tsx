import type { Recommendation } from '../../../types';
import { severityClass } from '../../../lib/stress';
import { StatusBadge } from '../../ui';

const PRIORITY_LABELS: Record<string, string> = {
  HIGH: 'High priority',
  MEDIUM: 'Medium priority',
  LOW: 'Low priority',
};

const PRIORITY_CLASS: Record<string, string> = {
  HIGH: 'status-bad',
  MEDIUM: 'status-warn',
  LOW: 'status-ok',
};

interface RecommendationsPanelProps {
  recommendations: Recommendation[];
}

export function RecommendationsPanel({ recommendations }: RecommendationsPanelProps) {
  if (recommendations.length === 0) {
    return (
      <p className="panel-hint">
        No recommendations. The grid shows no actionable stress conditions.
      </p>
    );
  }

  return (
    <ul className="stress-recommendations">
      {recommendations.map((rec) => (
        <li key={rec.id} className="stress-recommendation">
          <div className="stress-recommendation-header">
            <strong>{rec.title}</strong>
            <StatusBadge className={PRIORITY_CLASS[rec.priority]}>
              {PRIORITY_LABELS[rec.priority]}
            </StatusBadge>
          </div>
          <p className="stress-recommendation-description">{rec.description}</p>
          {rec.suggested_actions.length > 0 ? (
            <div className="stress-actions">
              <h4 className="stress-subheading">Suggested actions</h4>
              <ul>
                {rec.suggested_actions.map((action) => (
                  <li key={action}>{action}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {rec.expected_effect.length > 0 ? (
            <div className="stress-actions">
              <h4 className="stress-subheading">Expected effect</h4>
              <ul>
                {rec.expected_effect.map((effect) => (
                  <li key={effect}>{effect}</li>
                ))}
              </ul>
            </div>
          ) : null}
          <div className="stress-recommendation-meta">
            <StatusBadge className={severityClass(rec.priority === 'HIGH' ? 'CRITICAL' : rec.priority === 'MEDIUM' ? 'WARNING' : 'NORMAL')}>
              {rec.confidence} confidence
            </StatusBadge>
            {rec.related_issue_ids.length > 0 ? (
              <span className="status-badge status-idle">
                {rec.related_issue_ids.length} related issue(s)
              </span>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}
