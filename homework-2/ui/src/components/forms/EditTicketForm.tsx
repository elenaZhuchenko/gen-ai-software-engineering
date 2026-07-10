import { useState, type FormEvent } from 'react';
import type {
  Ticket,
  TicketUpdate,
  Category,
  Priority,
  Status,
} from '../../types/ticket';

interface EditTicketFormProps {
  ticket: Ticket;
  onSubmit: (data: TicketUpdate) => void;
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

export function EditTicketForm({
  ticket,
  onSubmit,
  isLoading,
}: EditTicketFormProps) {
  const [form, setForm] = useState<TicketUpdate>({
    subject: ticket.subject,
    description: ticket.description,
    category: ticket.category,
    priority: ticket.priority,
    status: ticket.status,
    assigned_to: ticket.assigned_to ?? '',
  });
  const [tagsInput, setTagsInput] = useState(ticket.tags.join(', '));

  function set<K extends keyof TicketUpdate>(key: K, value: TicketUpdate[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit({
      ...form,
      assigned_to: (form.assigned_to as string)?.trim() || null,
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
      <div>
        <label className={LABEL}>Subject *</label>
        <input
          className={INPUT}
          required
          maxLength={200}
          value={form.subject ?? ''}
          onChange={(e) => set('subject', e.target.value)}
        />
      </div>

      <div>
        <label className={LABEL}>Description *</label>
        <textarea
          className={`${INPUT} resize-none`}
          required
          minLength={10}
          maxLength={2000}
          rows={5}
          value={form.description ?? ''}
          onChange={(e) => set('description', e.target.value)}
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
            <option value="">None</option>
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
            <option value="">None</option>
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
            value={form.status ?? ''}
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
        <label className={LABEL}>Assigned To</label>
        <input
          className={INPUT}
          value={(form.assigned_to as string) ?? ''}
          onChange={(e) => set('assigned_to', e.target.value)}
          placeholder="agent-42"
        />
      </div>

      <div>
        <label className={LABEL}>Tags (comma-separated)</label>
        <input
          className={INPUT}
          value={tagsInput}
          onChange={(e) => setTagsInput(e.target.value)}
        />
      </div>

      <div className="flex justify-end pt-2">
        <button
          type="submit"
          disabled={isLoading}
          className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {isLoading ? 'Saving…' : 'Save Changes'}
        </button>
      </div>
    </form>
  );
}
