import type { Category, Priority, Status } from '../../types/ticket';

type BadgeValue = Category | Priority | Status;

const STYLES: Record<string, string> = {
  urgent: 'bg-red-100 text-red-800 ring-red-200',
  high: 'bg-orange-100 text-orange-800 ring-orange-200',
  medium: 'bg-yellow-100 text-yellow-800 ring-yellow-200',
  low: 'bg-green-100 text-green-800 ring-green-200',
  new: 'bg-blue-100 text-blue-800 ring-blue-200',
  in_progress: 'bg-indigo-100 text-indigo-800 ring-indigo-200',
  waiting_customer: 'bg-amber-100 text-amber-800 ring-amber-200',
  resolved: 'bg-emerald-100 text-emerald-800 ring-emerald-200',
  closed: 'bg-gray-100 text-gray-600 ring-gray-200',
  account_access: 'bg-purple-100 text-purple-800 ring-purple-200',
  technical_issue: 'bg-red-100 text-red-800 ring-red-200',
  billing_question: 'bg-sky-100 text-sky-800 ring-sky-200',
  feature_request: 'bg-teal-100 text-teal-800 ring-teal-200',
  bug_report: 'bg-rose-100 text-rose-800 ring-rose-200',
  other: 'bg-gray-100 text-gray-600 ring-gray-200',
};

const LABELS: Record<string, string> = {
  account_access: 'Account',
  technical_issue: 'Technical',
  billing_question: 'Billing',
  feature_request: 'Feature',
  bug_report: 'Bug',
  other: 'Other',
  new: 'New',
  in_progress: 'In Progress',
  waiting_customer: 'Waiting',
  resolved: 'Resolved',
  closed: 'Closed',
  urgent: 'Urgent',
  high: 'High',
  medium: 'Medium',
  low: 'Low',
};

interface BadgeProps {
  value: BadgeValue | null | undefined;
}

export function Badge({ value }: BadgeProps) {
  if (!value) return <span className="text-gray-400 text-xs">—</span>;
  const cls = STYLES[value] ?? 'bg-gray-100 text-gray-600 ring-gray-200';
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${cls}`}
    >
      {LABELS[value] ?? value}
    </span>
  );
}
