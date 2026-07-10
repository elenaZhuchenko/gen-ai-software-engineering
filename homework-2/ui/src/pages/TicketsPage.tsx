import { useState, useMemo } from 'react';
import {
  useTickets,
  useCreateTicket,
  useUpdateTicket,
  useDeleteTicket,
} from '../hooks/useTickets';
import { useAutoClassify } from '../hooks/useAutoClassify';
import { useToast } from '../components/shared/Toast';
import {
  TicketFilters,
  type FilterState,
} from '../components/tickets/TicketFilters';
import { TicketTable } from '../components/tickets/TicketTable';
import { SlideOver } from '../components/shared/SlideOver';
import { Modal } from '../components/shared/Modal';
import { Badge } from '../components/shared/Badge';
import { CreateTicketForm } from '../components/forms/CreateTicketForm';
import { EditTicketForm } from '../components/forms/EditTicketForm';
import type {
  Ticket,
  TicketCreate,
  TicketUpdate,
  ClassificationResult,
} from '../types/ticket';

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
        {label}
      </dt>
      <dd className="text-sm text-gray-800">{children}</dd>
    </div>
  );
}

export function TicketsPage() {
  const { data, isLoading } = useTickets();
  const { toast } = useToast();

  const createMutation = useCreateTicket();
  const updateMutation = useUpdateTicket();
  const deleteMutation = useDeleteTicket();
  const classifyMutation = useAutoClassify();

  const [filters, setFilters] = useState<FilterState>({
    category: '',
    priority: '',
    status: '',
  });
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [classifyResult, setClassifyResult] =
    useState<ClassificationResult | null>(null);

  const filtered = useMemo(() => {
    let list = data?.tickets ?? [];
    if (filters.category) list = list.filter((t) => t.category === filters.category);
    if (filters.priority) list = list.filter((t) => t.priority === filters.priority);
    if (filters.status) list = list.filter((t) => t.status === filters.status);
    return list;
  }, [data, filters]);

  function handleCreate(formData: TicketCreate) {
    createMutation.mutate(formData, {
      onSuccess: () => {
        toast('Ticket created successfully');
        setShowCreate(false);
      },
      onError: (err: unknown) => {
        const msg =
          (err as { response?: { data?: { detail?: string } } })?.response
            ?.data?.detail ?? 'Failed to create ticket';
        toast(msg, 'error');
      },
    });
  }

  function handleUpdate(formData: TicketUpdate) {
    if (!selectedTicket) return;
    updateMutation.mutate(
      { id: selectedTicket.id, data: formData },
      {
        onSuccess: (updated) => {
          toast('Ticket updated');
          setSelectedTicket(updated);
          setIsEditing(false);
        },
        onError: () => toast('Failed to update ticket', 'error'),
      },
    );
  }

  function handleDelete() {
    if (!selectedTicket) return;
    if (!confirm(`Delete ticket "${selectedTicket.subject}"?`)) return;
    deleteMutation.mutate(selectedTicket.id, {
      onSuccess: () => {
        toast('Ticket deleted');
        setSelectedTicket(null);
      },
      onError: () => toast('Failed to delete ticket', 'error'),
    });
  }

  function handleAutoClassify() {
    if (!selectedTicket) return;
    setClassifyResult(null);
    classifyMutation.mutate(
      { id: selectedTicket.id, override: true },
      {
        onSuccess: (result) => {
          setClassifyResult(result);
          toast('Classification complete');
          setSelectedTicket((prev) =>
            prev
              ? { ...prev, category: result.category, priority: result.priority }
              : prev,
          );
        },
        onError: () => toast('Classification failed', 'error'),
      },
    );
  }

  function openTicket(ticket: Ticket) {
    setSelectedTicket(ticket);
    setIsEditing(false);
    setClassifyResult(null);
  }

  const slideTitle = selectedTicket
    ? isEditing
      ? `Edit: ${selectedTicket.subject}`
      : selectedTicket.subject
    : '';

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tickets</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {filtered.length} of {data?.total ?? 0} tickets
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          New Ticket
        </button>
      </div>

      <div className="mb-4">
        <TicketFilters filters={filters} onChange={setFilters} />
      </div>

      <div className="bg-white rounded-xl border border-gray-200">
        {isLoading ? (
          <div className="p-8 space-y-3 animate-pulse">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded" />
            ))}
          </div>
        ) : (
          <TicketTable
            tickets={filtered}
            selectedId={selectedTicket?.id ?? null}
            onSelect={openTicket}
          />
        )}
      </div>

      <SlideOver
        open={!!selectedTicket}
        onClose={() => {
          setSelectedTicket(null);
          setIsEditing(false);
          setClassifyResult(null);
        }}
        title={slideTitle}
      >
        {selectedTicket && !isEditing && (
          <div className="space-y-6">
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setIsEditing(true)}
                className="px-3 py-1.5 text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                Edit
              </button>
              <button
                onClick={handleAutoClassify}
                disabled={classifyMutation.isPending}
                className="px-3 py-1.5 text-xs font-medium bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg transition-colors"
              >
                {classifyMutation.isPending ? 'Classifying…' : 'Auto-classify'}
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
                className="px-3 py-1.5 text-xs font-medium bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white rounded-lg transition-colors"
              >
                Delete
              </button>
            </div>

            {classifyResult && (
              <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 space-y-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge value={classifyResult.category} />
                  <Badge value={classifyResult.priority} />
                  <span className="text-xs text-indigo-500 ml-auto">
                    {Math.round(classifyResult.confidence * 100)}% confidence
                  </span>
                </div>
                <p className="text-xs text-indigo-700">{classifyResult.reasoning}</p>
                {classifyResult.keywords_found.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {classifyResult.keywords_found.map((k) => (
                      <span
                        key={k}
                        className="bg-indigo-100 text-indigo-700 text-xs px-2 py-0.5 rounded-full"
                      >
                        {k}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}

            <dl className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <Badge value={selectedTicket.category} />
                <Badge value={selectedTicket.priority} />
                <Badge value={selectedTicket.status} />
              </div>
              <Field label="Customer">
                {selectedTicket.customer_name} ({selectedTicket.customer_email})
              </Field>
              <Field label="Customer ID">{selectedTicket.customer_id}</Field>
              <Field label="Description">
                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                  {selectedTicket.description}
                </p>
              </Field>
              {selectedTicket.assigned_to && (
                <Field label="Assigned To">{selectedTicket.assigned_to}</Field>
              )}
              {selectedTicket.tags.length > 0 && (
                <Field label="Tags">
                  <div className="flex flex-wrap gap-1">
                    {selectedTicket.tags.map((tag) => (
                      <span
                        key={tag}
                        className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </Field>
              )}
              <Field label="Created">
                {new Date(selectedTicket.created_at).toLocaleString()}
              </Field>
              <Field label="Updated">
                {new Date(selectedTicket.updated_at).toLocaleString()}
              </Field>
              {selectedTicket.resolved_at && (
                <Field label="Resolved">
                  {new Date(selectedTicket.resolved_at).toLocaleString()}
                </Field>
              )}
              <Field label="Source">{selectedTicket.metadata.source}</Field>
              {selectedTicket.metadata.device_type && (
                <Field label="Device">
                  {selectedTicket.metadata.device_type}
                </Field>
              )}
            </dl>
          </div>
        )}

        {selectedTicket && isEditing && (
          <div>
            <button
              onClick={() => setIsEditing(false)}
              className="text-xs text-gray-500 hover:text-gray-700 mb-4 flex items-center gap-1"
            >
              ← Back to details
            </button>
            <EditTicketForm
              ticket={selectedTicket}
              onSubmit={handleUpdate}
              isLoading={updateMutation.isPending}
            />
          </div>
        )}
      </SlideOver>

      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title="New Ticket"
      >
        <CreateTicketForm
          onSubmit={handleCreate}
          isLoading={createMutation.isPending}
        />
      </Modal>
    </div>
  );
}
