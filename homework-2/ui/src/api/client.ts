import axios from 'axios';
import type {
  Ticket,
  TicketCreate,
  TicketUpdate,
  TicketListResponse,
  ClassificationResult,
  ImportSummary,
  TicketFilters,
} from '../types/ticket';

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000',
});

export async function getTickets(filters?: TicketFilters): Promise<TicketListResponse> {
  const { data } = await api.get<TicketListResponse>('/tickets', { params: filters });
  return data;
}

export async function getTicket(id: string): Promise<Ticket> {
  const { data } = await api.get<Ticket>(`/tickets/${id}`);
  return data;
}

export async function createTicket(payload: TicketCreate): Promise<Ticket> {
  const { data } = await api.post<Ticket>('/tickets', payload);
  return data;
}

export async function updateTicket(id: string, payload: TicketUpdate): Promise<Ticket> {
  const { data } = await api.put<Ticket>(`/tickets/${id}`, payload);
  return data;
}

export async function deleteTicket(id: string): Promise<void> {
  await api.delete(`/tickets/${id}`);
}

export async function autoClassify(
  id: string,
  override = false,
): Promise<ClassificationResult> {
  const { data } = await api.post<ClassificationResult>(
    `/tickets/${id}/auto-classify`,
    { override },
  );
  return data;
}

export async function importTickets(
  file: File,
  autoClassifyFlag = false,
): Promise<ImportSummary> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post<ImportSummary>('/tickets/import', form, {
    params: { auto_classify: autoClassifyFlag },
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}
