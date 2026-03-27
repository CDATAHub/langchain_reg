import React, { useState, useEffect, useCallback } from 'react';
import { queryAPI, type QueryResponse, type SourceDocument } from '../services/api';

interface UseStreamingQueryOptions {
  onChunk?: (chunk: string) => void;
  onComplete?: (response: QueryResponse) => void;
  onError?: (error: Error) => void;
}

export function useStreamingQuery(options: UseStreamingQueryOptions = {}) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [sources, setSources] = useState<SourceDocument[]>([]);
  const [chunks, setChunks] = useState<string[]>([]);
  const [completeResponse, setCompleteResponse] = useState<QueryResponse | null>(null);

  const reset = useCallback(() => {
    setIsStreaming(false);
    setError(null);
    setSources([]);
    setChunks([]);
    setCompleteResponse(null);
  }, []);

  const executeQuery = useCallback(async (
    question: string,
    stream: boolean = true,
    topK: number = 5
  ): Promise<QueryResponse | null> => {
    reset();

    try {
      setIsStreaming(true);

      if (stream) {
        // Streaming query
        const response = await queryAPI.streamQuery({
          question,
          stream,
          top_k: topK,
        });

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('Failed to read stream');
        }

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              try {
                const event = JSON.parse(data);

                if (event.type === 'sources') {
                  setSources(event.data || []);
                } else if (event.type === 'chunk') {
                  setChunks(prev => [...prev, event.content]);
                  options.onChunk?.(event.content);
                } else if (event.type === 'error') {
                  throw new Error(event.message || 'Stream error');
                } else if (event.type === 'end') {
                  setIsStreaming(false);
                  options.onComplete?.(completeResponse!);
                }
              } catch (e) {
                console.error('Error parsing SSE:', e);
              }
            }
          }
        }
      } else {
        // Non-streaming query
        const response = await queryAPI.queryDocuments({
          question,
          stream,
          top_k: topK,
        });

        setCompleteResponse(response);
        setSources(response.sources);
        options.onComplete?.(response);
      }

      return completeResponse;
    } catch (err) {
      const error = err as Error;
      setError(error);
      options.onError?.(error);
      setIsStreaming(false);
      return null;
    }
  }, [reset, options, completeResponse]);

  return {
    executeQuery,
    isStreaming,
    error,
    sources,
    chunks,
    completeResponse,
    reset,
  };
}