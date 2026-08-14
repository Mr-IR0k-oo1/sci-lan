import type { ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  icon?: ReactNode;
}

export function Button({
  variant = 'secondary',
  icon,
  children,
  className,
  ...rest
}: ButtonProps) {
  const variantClass = `btn btn-${variant}`;
  return (
    <button className={`${variantClass}${className ? ` ${className}` : ''}`} {...rest}>
      {icon ? <span className="btn-icon">{icon}</span> : null}
      {children}
    </button>
  );
}

export function Section({
  title,
  action,
  children,
}: {
  title: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="panel-section">
      <div className="panel-section-header">
        <h3>{title}</h3>
        {action}
      </div>
      {children}
    </div>
  );
}

export function StatusBadge({ className, children }: { className: string; children: ReactNode }) {
  return <span className={`status-badge ${className}`}>{children}</span>;
}

export function Spinner({ label }: { label: string }) {
  return (
    <span className="spinner" role="status">
      <span className="spinner-icon" aria-hidden="true" />
      {label}
    </span>
  );
}
