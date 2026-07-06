import type { Ticket } from '../../types/ticket';
import { TicketRow } from './TicketRow';

interface TicketTableProps {
  tickets: Ticket[];
  selectedId: string | null;
  onSelect: (ticket: Ticket) => void;
}

const COLS = ['#', 'Customer', 'Subject', 'Category', 'Priority', 'Status', 'Created'];

export function TicketTable({ tickets, selectedId, onSelect }: TicketTableProps) {
  if (tickets.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          <svg
            className="w-8 h-8 text-gray-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
        </div>
        <p className="text-gray-500 font-medium">No tickets found</p>
        <p className="text-gray-400 text-sm mt-1">
          Create a ticket or adjust your filters
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 bg-gray-50">
            {COLS.map((col) => (
              <th
                key={col}
                className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tickets.map((ticket) => (
            <TicketRow
              key={ticket.id}
              ticket={ticket}
              isSelected={ticket.id === selectedId}
              onClick={() => onSelect(ticket)}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
