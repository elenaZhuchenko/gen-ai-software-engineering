export type Category =
  | 'account_access'
  | 'technical_issue'
  | 'billing_question'
  | 'feature_request'
  | 'bug_report'
  | 'other';

export type Priority = 'urgent' | 'high' | 'medium' | 'low';

export type Status =
  | 'new'
  | 'in_progress'
  | 'waiting_customer'
  | 'resolved'
  | 'closed';

export type Source = 'web_form' | 'email' | 'api' | 'chat' | 'phone';

export type DeviceType = 'desktop' | 'mobile' | 'tablet';

export interface TicketMetadata {
  source: Source;
  browser: string | null;
  device_type: DeviceType | null;
}

export interface ClassificationResult {
  category: Category;
  priority: Priority;
  confidence: number;
  reasoning: string;
  keywords_found: string[];
  classified_at: string;
  manual_override: boolean;
}

export interface Ticket {
  id: string;
  customer_id: string;
  customer_email: string;
  customer_name: string;
  subject: string;
  description: string;
  category: Category | null;
  priority: Priority | null;
  status: Status;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  assigned_to: string | null;
  tags: string[];
  metadata: TicketMetadata;
  classification: ClassificationResult | null;
}

export interface TicketCreate {
  customer_id: string;
  customer_email: string;
  customer_name: string;
  subject: string;
  description: string;
  category?: Category | null;
  priority?: Priority | null;
  status?: Status;
  assigned_to?: string | null;
  tags?: string[];
  metadata?: Partial<TicketMetadata>;
  auto_classify?: boolean;
}

export interface TicketUpdate {
  customer_id?: string;
  customer_email?: string;
  customer_name?: string;
  subject?: string;
  description?: string;
  category?: Category | null;
  priority?: Priority | null;
  status?: Status;
  assigned_to?: string | null;
  tags?: string[];
  metadata?: Partial<TicketMetadata>;
  resolved_at?: string | null;
}

export interface TicketListResponse {
  total: number;
  tickets: Ticket[];
}

export interface ImportSummary {
  total: number;
  successful: number;
  failed: number;
  errors: Array<{ row: number; error: string }>;
  tickets: Ticket[];
}

export interface TicketFilters {
  category?: Category;
  priority?: Priority;
  status?: Status;
  customer_id?: string;
}
