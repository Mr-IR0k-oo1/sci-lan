import type { ReactNode } from 'react';

const base = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
} as const;

export function PlayIcon(): ReactNode {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
      <polygon points="6 4 20 12 6 20" {...base} />
    </svg>
  );
}

export function PlusIcon(): ReactNode {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
      <line x1="12" y1="5" x2="12" y2="19" {...base} />
      <line x1="5" y1="12" x2="19" y2="12" {...base} />
    </svg>
  );
}

export function SaveIcon(): ReactNode {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
      <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" {...base} />
      <polyline points="17 21 17 13 7 13 7 21" {...base} />
      <polyline points="7 3 7 8 15 8" {...base} />
    </svg>
  );
}

export function LineIcon(): ReactNode {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
      <path d="M4 20 20 4" {...base} />
      <circle cx="4" cy="20" r="2.5" {...base} />
      <circle cx="20" cy="4" r="2.5" {...base} />
    </svg>
  );
}

export function ErrorIcon(): ReactNode {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">
      <circle cx="12" cy="12" r="10" {...base} />
      <line x1="12" y1="8" x2="12" y2="12" {...base} />
      <line x1="12" y1="16" x2="12.01" y2="16" {...base} />
    </svg>
  );
}

export function WarningIcon(): ReactNode {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">
      <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" {...base} />
      <line x1="12" y1="9" x2="12" y2="13" {...base} />
      <line x1="12" y1="17" x2="12.01" y2="17" {...base} />
    </svg>
  );
}

export function CheckIcon(): ReactNode {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">
      <polyline points="20 6 9 17 4 12" {...base} />
    </svg>
  );
}

export function RefreshIcon(): ReactNode {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
      <polyline points="23 4 23 10 17 10" {...base} />
      <path d="M20.5 15a9 9 0 1 1-2-9.4L23 10" {...base} />
    </svg>
  );
}

export function TrashIcon(): ReactNode {
  return (
    <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">
      <polyline points="3 6 5 6 21 6" {...base} />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" {...base} />
    </svg>
  );
}
