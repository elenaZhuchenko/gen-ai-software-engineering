import { useState, type FormEvent } from 'react';
import type {
  TicketCreate,
  Category,
  Priority,
  Status,
} from '../../types/ticket';

interface CreateTicketFormProps {
  onSubmit: (data: TicketCreate) => void;
  isLoading: boolean;
}

const CATEGORIES: Category[] = [
  'account_access',
  'technical_issue',
  'billing_question',
  'feature_request',
  'bug_report',
  'other',
];
const PRIORITIES: Priority[] = ['urgent', 'high', 'medium', 'low'];
const STATUSES: Status[] = [
  'new',
  'in_progress',
  'waiting_customer',
  'resolved',
  'closed',
];

const INPUT =
  'w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent';
const LABEL = 'block text-xs font-medium text-gray-600 mb-1';

export function CreateTicketForm({
  onSubmit,
  isLoading,
}: CreateTicketFormProps) {
  const [form, setForm] = useState<TicketCreate>({
    customer_id: '',
    customer_email: '',
    customer_name: '',
    subject: '',
    description: '',
    category: null,
    priority: null,
    status: 'new',
    tags: [],
    auto_classify: true,
  });
  const [tagsInput, setTagsInput] = useState('');

  function set<K extends keyof TicketCreate>(key: K, value: TicketCreate[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit({
      ...form,
      tags: tagsInput
        ? tagsInput
            .split(',')
            .map((t) => t.trim())
            .filter(Boolean)
        : [],
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={LABEL}>Customer ID *</label>
          <input
            className={INPUT}
            required
            value={form.customer_id}
            onChange={(e) => set('customer_id', e.target.value)}
            placeholder="cust-1001"
          />
        </div>
        <div>
          <label className={LABEL}>Customer Name *</label>
          <input
            className={INPUT}
            required
            value={form.customer_name}
            onChange={(e) => set('customer_name', e.target.value)}
            placeholder="Alex Rivera"
          />
        </div>
      </div>

      <div>
        <label className={LABEL}>Customer Email *</label>
        <input
          className={INPUT}
          required
          type="email"
          value={form.customer_email}
          onChange={(e) => set('customer_email', e.target.value)}
          placeholder="alex@example.com"
        />
      </div>

      <div>
        <label className={LABEL}>Subject * (max 200 chars)</label>
        <input
          className={INPUT}
          required
          maxLength={200}
          value={form.subject}
          onChange={(e) => set('subject', e.target.value)}
          placeholder="Brief description of the issue"
        />
      </div>

      <div>
        <label className={LABEL}>Description * (min 10 chars)</label>
        <textarea
          className={`${INPUT} resize-none`}
          required
          minLength={10}
          maxLength={2000}
          rows={4}
          value={form.description}
          onChange={(e) => set('description', e.target.value)}
          placeholder="Detailed description of the issue..."
        />
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className={LABEL}>Category</label>
          <select
            className={INPUT}
            value={form.category ?? ''}
            onChange={(e) =>
              set('category', (e.target.value as Category) || null)
            }
          >
            <option value="">Auto-detect</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className={LABEL}>Priority</label>
          <select
            className={INPUT}
            value={form.priority ?? ''}
            onChange={(e) =>
              set('priority', (e.target.value as Priority) || null)
            }
          >
            <option value="">Auto-detect</option>
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className={LABEL}>Status</label>
          <select
            className={INPUT}
            value={form.status ?? 'new'}
            onChange={(e) => set('status', e.target.value as Status)}
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label className={LABEL}>Tags (comma-separated)</label>
        <input
          className={INPUT}
          value={tagsInput}
          onChange={(e) => setTagsInput(e.target.value)}
          placeholder="login, vip"
        />
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="auto_classify"
          checked={form.auto_classify}
          onChange={(e) => set('auto_classify', e.target.checked)}
          className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
        />
        <label htmlFor="auto_classify" className="text-sm text-gray-700">
          Auto-classify on create
        </label>
      </div>

      <div className="flex justify-end pt-2">
        <button
          type="submit"
          disabled={isLoading}
          className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {isLoading ? 'Creating…' : 'Create Ticket'}
        </button>
      </div>
    </form>
  );
}
