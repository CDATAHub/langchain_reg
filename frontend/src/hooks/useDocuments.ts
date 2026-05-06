import { useState, useCallback, useEffect } from 'react';
import { documentAPI, type DocumentMetadata, type DocumentList, type UploadResponse } from '../services/api';

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [indexStatus, setIndexStatus] = useState<DocumentMetadata | null>(null);

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response: DocumentList = await documentAPI.listDocuments();
      setDocuments(response.documents);
    } catch (err) {
      setError('Failed to load documents');
      console.error('Error loading documents:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const uploadDocument = useCallback(async (
    file: File,
    indexAfterUpload: boolean = true
  ): Promise<UploadResponse> => {
    setLoading(true);
    setError(null);

    try {
      const response = await documentAPI.uploadFile(file, indexAfterUpload);

      // Reload documents after upload
      await loadDocuments();
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to upload document';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadDocuments]);

  const rebuildIndex = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      await documentAPI.rebuildIndex();
      await loadDocuments();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to rebuild index';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadDocuments]);

  const getIndexStatus = useCallback(async () => {
    try {
      const status = await documentAPI.getIndexStatus();
      setIndexStatus(status);
      return status;
    } catch (err) {
      console.error('Error getting index status:', err);
      return null;
    }
  }, []);

  // Load documents on component mount
  useEffect(() => {
    loadDocuments();
    getIndexStatus();
  }, [loadDocuments, getIndexStatus]);

  return {
    documents,
    loading,
    error,
    indexStatus,
    loadDocuments,
    uploadDocument,
    rebuildIndex,
    getIndexStatus,
  };
}