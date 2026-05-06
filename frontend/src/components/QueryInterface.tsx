import React, { useState, useRef, useEffect } from 'react';
import { useStreamingQuery, useDocuments } from '../hooks';
import { type SourceDocument } from '../services/api';
import { WebSocketManager } from '../services/websocket';
import { getOrCreateSessionId } from '../services/api';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/ws/';

const QueryInterface: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [useStreaming, setUseStreaming] = useState(true);
  const [topK, setTopK] = useState(5);
  const [isWebSocketConnected, setIsWebSocketConnected] = useState(false);
  const [wsError, setWsError] = useState<string | null>(null);

  const wsRef = useRef<WebSocketManager | null>(null);
  const messageContainerRef = useRef<HTMLDivElement>(null);

  const {
    isStreaming: queryLoading,
    error: queryError,
    sources,
    chunks,
    reset: resetQuery,
    executeQuery
  } = useStreamingQuery({
    onChunk: (_chunk) => {
      // Auto-scroll to bottom
      if (messageContainerRef.current) {
        messageContainerRef.current.scrollTop = messageContainerRef.current.scrollHeight;
      }
    },
    onComplete: (response) => {
      console.log('Query completed:', response);
    },
    onError: (error) => {
      console.error('Query error:', error);
    }
  });

  const { uploadDocument } = useDocuments();

  // Initialize WebSocket
  useEffect(() => {
    try {
      getOrCreateSessionId();
      wsRef.current = new WebSocketManager(WS_URL, {
        onMessage: (message) => {
          console.log('WebSocket message:', message);
          
          switch (message.type) {
            case 'connected':
              setIsWebSocketConnected(true);
              setWsError(null); // 清除错误
              break;
            case 'error':
              setWsError(message.message || '发生未知错误');
              console.error('WebSocket error message:', message);
              break;
            default:
              setWsError(null); // 收到其他消息时清除错误
          }
        },
        onConnect: () => {
          setIsWebSocketConnected(true);
        },
        onDisconnect: () => {
          setIsWebSocketConnected(false);
        },
        onError: (error) => {
          console.error('WebSocket error:', error);
          setIsWebSocketConnected(false);
        }
      });

      wsRef.current.connect();
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      setIsWebSocketConnected(false);
    }

    return () => {
      wsRef.current?.disconnect();
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setWsError(null); // 清除之前的错误
    
    resetQuery();

    try {
      await executeQuery(question, useStreaming, topK);
    } catch (error) {
      console.error('Query failed:', error);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      await uploadDocument(file);
      alert('Document uploaded successfully!');
    } catch (error) {
      alert('Failed to upload document');
      console.error('Upload error:', error);
    }
  };

  const formatConfidence = (confidence: number) => {
    return (confidence * 100).toFixed(1) + '%';
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">保险文档智能问答</h1>

      {/* WebSocket Status */}
      <div className={`flex items-center space-x-2 ${isWebSocketConnected ? 'text-green-600' : 'text-red-600'}`}>
        <div className={`w-2 h-2 rounded-full ${isWebSocketConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
        <span className="text-sm">
          {isWebSocketConnected ? '实时连接已建立' : 'WebSocket 未连接'}
        </span>
      </div>

      {/* WebSocket Error Display */}
      {wsError && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-md">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-red-700">{wsError}</p>
            </div>
            <button
              onClick={() => setWsError(null)}
              className="ml-auto text-red-500 hover:text-red-700"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Query Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6">
        <div className="space-y-4">
          <div>
            <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-1">
              您的问题
            </label>
            <textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="请输入您关于保险产品的问题..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="streaming" className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="streaming"
                  checked={useStreaming}
                  onChange={(e) => setUseStreaming(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                />
                <span className="text-sm text-gray-700">实时回答</span>
              </label>
            </div>

            <div>
              <label htmlFor="topK" className="block text-sm font-medium text-gray-700 mb-1">
                检索文档数
              </label>
              <select
                id="topK"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value={3}>3</option>
                <option value={5}>5</option>
                <option value={10}>10</option>
              </select>
            </div>
          </div>

          <div className="flex justify-between items-center">
            <div className="flex space-x-2">
              <label className="inline-flex items-center px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm cursor-pointer">
                <span>上传文档</span>
                <input
                  type="file"
                  accept=".txt,.pdf,.md"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="ml-2 hover:text-blue-600">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </label>
              </label>
            </div>

            <button
              type="submit"
              disabled={queryLoading || !question.trim()}
              className={`px-6 py-2 rounded-md text-white font-medium ${
                queryLoading || !question.trim()
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
              }`}
            >
              {queryLoading ? '回答中...' : '提问'}
            </button>
          </div>
        </div>
      </form>

      {/* Error Display */}
      {queryError && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-md">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-red-700">{queryError.message}</p>
            </div>
          </div>
        </div>
      )}

      {/* Answer Display */}
      {chunks.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">AI 回答</h2>
          <div
            ref={messageContainerRef}
            className="prose prose-sm max-w-none"
          >
            {chunks.map((chunk, index) => (
              <span key={index} className="text-gray-800">
                {chunk}
              </span>
            ))}
          </div>
          <div className="mt-4 flex items-center space-x-2 text-sm text-gray-500">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
            <span>最后更新: {new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      )}

      {/* Sources Display */}
      {sources.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">参考文档</h2>
          <div className="space-y-3">
            {sources.map((source: SourceDocument, index: number) => (
              <div key={index} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-gray-900 truncate">
                    {source.file_name}
                  </h3>
                  <span className="text-xs text-gray-500">
                    相似度: {formatConfidence(source.score || 0)}
                  </span>
                </div>
                <p className="text-sm text-gray-600 line-clamp-3">
                  {source.content}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default QueryInterface;
