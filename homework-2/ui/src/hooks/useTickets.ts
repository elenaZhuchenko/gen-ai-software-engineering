import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getTickets,
  createTicket,
  updateTicket,
  deleteTicket,
} from '../api/client';
import type { TicketFilters, TicketCreate, TicketUpdate } from '../types/ticket';

export function useTickets(filters?: TicketFilters) {
  return useQuery({
    queryKey: ['tickets', filters],
    queryFn: () => getTickets(filters),
  });
}

export function useCreateTicket() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TicketCreate) => createTicket(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tickets'] }),
  });
}

export function useUpdateTicket() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TicketUpdate }) =>
      updateTicket(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tickets'] }),
  });
}

export function useDeleteTicket() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteTicket(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tickets'] }),
  });
}
