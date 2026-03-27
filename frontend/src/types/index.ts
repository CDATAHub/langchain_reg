export interface SourceDocument {
  content: string;
  file_name: string;
  score?: number;
  page_number?: number;
}

export interface QueryResponse {
  answer: string;
  sources: SourceDocument[];
  confidence: number;
  timestamp: string;
}

export interface DocumentMetadata {
  file_name: string;
  size: number;
  uploaded_at: string;
  indexed?: boolean;
  chunks_count?: number;
}

export interface DocumentList {
  documents: DocumentMetadata[];
  total_count: number;
}

export interface UploadResponse {
  message: string;
  file_name: string;
  file_size: number;
  file_path: string;
  uploaded_at: string;
}

export interface ReportRequest {
  question: string;
  answer: string;
  sources: string[];
  report_type?: 'structured' | 'detailed';
  send_email?: boolean;
  email_recipient?: string;
}

export interface ReportResponse {
  report_id: string;
  report_content: string;
  timestamp: string;
  file_path?: string;
  email_sent?: boolean;
}

export interface WebSocketMessage {
  type: 'query' | 'stream' | 'status' | 'error' | 'sources' | 'chunk' | 'end' | 'pong';
  data?: any;
  message?: string;
}

export interface QueryParams {
  question: string;
  stream?: boolean;
  top_k?: number;
}

export interface ConnectionStatus {
  connected: boolean;
  session_id?: string;
  message?: string;
}
