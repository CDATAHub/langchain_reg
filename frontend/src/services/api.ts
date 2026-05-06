import axios from 'axios';

// Define types inline to avoid import issues
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
  trace_id?: string;
  session_id?: string;
}

export interface DocumentMetadata {
  file_name: string;
  size: number;
  uploaded_at: string;
  indexed?: boolean;
  chunks_count?: number;
  storage_path?: string;
  last_updated?: string;
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

export interface QueryParams {
  question: string;
  stream?: boolean;
  top_k?: number;
  session_id?: string;
}

export function getOrCreateSessionId(): string {
  const storageKey = 'rag_session_id';
  const existing = window.localStorage.getItem(storageKey);
  if (existing) {
    return existing;
  }

  const created = `sess_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  window.localStorage.setItem(storageKey, created);
  return created;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Document API
export const documentAPI = {
  async listDocuments(): Promise<DocumentList> {
    const response = await api.get<DocumentList>('/api/documents/');
    return response.data;
  },

  async uploadFile(file: File, indexAfterUpload = true): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const params = {
      index_after_upload: indexAfterUpload
    };

    const response = await api.post<UploadResponse>(
      '/api/upload/file',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        params,
      }
    );
    return response.data;
  },

  async getIndexStatus(): Promise<DocumentMetadata> {
    const response = await api.get<DocumentMetadata>('/api/documents/status');
    return response.data;
  },

  async rebuildIndex(): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>('/api/documents/rebuild-index');
    return response.data;
  },
};

// Query API
export const queryAPI = {
  async queryDocuments(params: QueryParams): Promise<QueryResponse> {
    const sessionId = params.session_id || getOrCreateSessionId();
    const response = await api.post<QueryResponse>('/api/queries/', {
      ...params,
      session_id: sessionId,
    }, {
      headers: {
        'X-Session-Id': sessionId,
      },
    });
    return response.data;
  },

  async streamQuery(params: QueryParams): Promise<Response> {
    const sessionId = params.session_id || getOrCreateSessionId();
    const response = await fetch(`${API_BASE_URL}/api/queries/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-Id': sessionId,
      },
      body: JSON.stringify({
        ...params,
        session_id: sessionId,
      }),
    });
    return response;
  },
};

// Report API
export const reportAPI = {
  async generateReport(request: ReportRequest): Promise<ReportResponse> {
    const response = await api.post<ReportResponse>('/api/reports/', request);
    return response.data;
  },

  async listReports(): Promise<{ reports: any[], total_count: number }> {
    const response = await api.get<{ reports: any[], total_count: number }>('/api/reports/list');
    return response.data;
  },

  async downloadReport(reportId: string): Promise<Blob> {
    const response = await api.get(`/api/reports/download/${reportId}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  async deleteReport(reportId: string): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(`/api/reports/delete/${reportId}`);
    return response.data;
  },
};

// Health check
export const healthAPI = {
  async checkHealth(): Promise<{ status: string; timestamp: string }> {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
