import type { Ticket } from '../../types/ticket';
import { Badge } from '../shared/Badge';

interface TicketRowProps {
  ticket: Ticket;
  onClick: () => void;
  isSelected: boolean;
}

export function TicketRow({ ticket, onClick, isSelected }: TicketRowProps) {
  const shortId = ticket.id.slice(-8);
  const date = new Date(ticket.created_at).toLocaleDateString();

  return (
    <tr
      onClick={onClick}
      className={`border-b border-gray-50 cursor-pointer transition-colors ${
        isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'
      }`}
    >
      <td className="px-5 py-3 text-xs text-gray-400 font-mono">
        #{shortId}
      </td>
      <td className="px-5 py-3">
        <div className="font-medium text-gray-900 text-sm">
          {ticket.customer_name}
        </div>
        <div className="text-xs text-gray-400">{ticket.customer_email}</div>
      </td>
      <td className="px-5 py-3 max-w-xs">
        <div className="text-sm text-gray-800 truncate">{ticket.subject}</div>
      </td>
      <td className="px-5 py-3">
        <Badge value={ticket.category} />
      </td>
      <td className="px-5 py-3">
        <Badge value={ticket.priority} />
      </td>
      <td className="px-5 py-3">
        <Badge value={ticket.status} />
      </td>
      <td className="px-5 py-3 text-xs text-gray-400 whitespace-nowrap">
        {date}
      </td>
    </tr>
  );
}
