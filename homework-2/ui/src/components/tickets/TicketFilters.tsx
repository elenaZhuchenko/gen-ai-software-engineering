import type { Category, Priority, Status } from '../../types/ticket';

const CATEGORIES: { value: Category; label: string }[] = [
  { value: 'account_access', label: 'Account Access' },
  { value: 'technical_issue', label: 'Technical Issue' },
  { value: 'billing_question', label: 'Billing' },
  { value: 'feature_request', label: 'Feature Request' },
  { value: 'bug_report', label: 'Bug Report' },
  { value: 'other', label: 'Other' },
];

const PRIORITIES: { value: Priority; label: string }[] = [
  { value: 'urgent', label: 'Urgent' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];

const STATUSES: { value: Status; label: string }[] = [
  { value: 'new', label: 'New' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'waiting_customer', label: 'Waiting' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'closed', label: 'Closed' },
];

export interface FilterState {
  category: Category | '';
  priority: Priority | '';
  status: Status | '';
}

interface TicketFiltersProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
}

const SELECT_CLS =
  'rounded-lg border border-gray-200 px-3 py-2 text-sm bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500';

export function TicketFilters({ filters, onChange }: TicketFiltersProps) {
  const { category, priority, status } = filters;
  const hasFilters = category !== '' || priority !== '' || status !== '';

  return (
    <div className="flex flex-wrap items-center gap-3">
      <select
        value={category}
        onChange={(e) =>
          onChange({ ...filters, category: e.target.value as Category | '' })
        }
        className={SELECT_CLS}
      >
        <option value="">All Categories</option>
        {CATEGORIES.map((c) => (
          <option key={c.value} value={c.value}>
            {c.label}
          </option>
        ))}
      </select>

      <select
        value={priority}
        onChange={(e) =>
          onChange({ ...filters, priority: e.target.value as Priority | '' })
        }
        className={SELECT_CLS}
      >
        <option value="">All Priorities</option>
        {PRIORITIES.map((p) => (
          <option key={p.value} value={p.value}>
            {p.label}
          </option>
        ))}
      </select>

      <select
        value={status}
        onChange={(e) =>
          onChange({ ...filters, status: e.target.value as Status | '' })
        }
        className={SELECT_CLS}
      >
        <option value="">All Statuses</option>
        {STATUSES.map((s) => (
          <option key={s.value} value={s.value}>
            {s.label}
          </option>
        ))}
      </select>

      {hasFilters && (
        <button
          onClick={() => onChange({ category: '', priority: '', status: '' })}
          className="text-xs text-gray-500 hover:text-gray-700 underline"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
