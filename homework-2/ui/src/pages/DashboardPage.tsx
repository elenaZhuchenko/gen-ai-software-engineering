import { Link } from 'react-router-dom';
import { useTickets } from '../hooks/useTickets';
import { Badge } from '../components/shared/Badge';
import type { Ticket, Category, Priority } from '../types/ticket';

const CATEGORIES: Category[] = [
  'account_access',
  'technical_issue',
  'billing_question',
  'feature_request',
  'bug_report',
  'other',
];

const PRIORITIES: Priority[] = ['urgent', 'high', 'medium', 'low'];

function countBy<T>(tickets: Ticket[], key: keyof Ticket, val: T): number {
  return tickets.filter((t) => t[key] === val).length;
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className={`rounded-xl p-5 text-white ${color}`}>
      <p className="text-3xl font-bold">{value}</p>
      <p className="text-sm font-medium mt-1 opacity-90">{label}</p>
    </div>
  );
}

function BarChart({
  items,
  total,
}: {
  items: { label: string; count: number }[];
  total: number;
}) {
  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-3">
          <div className="w-32 text-right text-xs text-gray-500 truncate capitalize">
            {item.label}
          </div>
          <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
            <div
              className="h-3 bg-blue-500 rounded-full transition-all duration-500"
              style={{
                width: total ? `${(item.count / total) * 100}%` : '0%',
              }}
            />
          </div>
          <div className="w-6 text-xs text-gray-600 font-medium text-right">
            {item.count}
          </div>
        </div>
      ))}
    </div>
  );
}

export function DashboardPage() {
  const { data, isLoading } = useTickets();
  const tickets = data?.tickets ?? [];
  const total = tickets.length;
  const open = tickets.filter(
    (t) => t.status === 'new' || t.status === 'in_progress',
  ).length;
  const urgent = countBy(tickets, 'priority', 'urgent');
  const resolved = tickets.filter(
    (t) => t.status === 'resolved' || t.status === 'closed',
  ).length;

  const recent = [...tickets]
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    )
    .slice(0, 5);

  if (isLoading) {
    return (
      <div className="p-8 animate-pulse space-y-4">
        <div className="h-8 w-48 bg-gray-200 rounded" />
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 bg-gray-200 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Tickets" value={total} color="bg-blue-600" />
        <StatCard label="Open" value={open} color="bg-indigo-600" />
        <StatCard label="Urgent" value={urgent} color="bg-red-500" />
        <StatCard
          label="Resolved / Closed"
          value={resolved}
          color="bg-green-600"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">
            By Category
          </h2>
          <BarChart
            total={total}
            items={CATEGORIES.map((c) => ({
              label: c.replace(/_/g, ' '),
              count: countBy(tickets, 'category', c),
            }))}
          />
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">
            By Priority
          </h2>
          <BarChart
            total={total}
            items={PRIORITIES.map((p) => ({
              label: p,
              count: countBy(tickets, 'priority', p),
            }))}
          />
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700">
            Recent Tickets
          </h2>
          <Link
            to="/tickets"
            className="text-xs text-blue-600 hover:underline"
          >
            View all →
          </Link>
        </div>
        {tickets.length === 0 ? (
          <div className="px-5 py-12 text-center text-gray-400 text-sm">
            <p>No tickets yet.</p>
            <Link
              to="/tickets"
              className="text-blue-500 hover:underline mt-1 inline-block"
            >
              Create your first ticket →
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b border-gray-100">
                  {['Subject', 'Customer', 'Priority', 'Status', 'Created'].map(
                    (h) => (
                      <th
                        key={h}
                        className="px-5 py-2 text-xs font-medium text-gray-500"
                      >
                        {h}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody>
                {recent.map((ticket) => (
                  <tr
                    key={ticket.id}
                    className="border-b last:border-0 border-gray-50"
                  >
                    <td className="px-5 py-3 max-w-xs truncate text-gray-900">
                      {ticket.subject}
                    </td>
                    <td className="px-5 py-3 text-gray-600">
                      {ticket.customer_name}
                    </td>
                    <td className="px-5 py-3">
                      <Badge value={ticket.priority} />
                    </td>
                    <td className="px-5 py-3">
                      <Badge value={ticket.status} />
                    </td>
                    <td className="px-5 py-3 text-gray-400 text-xs whitespace-nowrap">
                      {new Date(ticket.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
