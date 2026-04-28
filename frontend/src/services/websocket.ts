import React, { useState, useEffect, useRef } from 'react';
import { type WebSocketMessage } from '../types';

interface WebSocketOptions {
  url?: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
  reconnect?: boolean;
  reconnectInterval?: number;
}

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private options: WebSocketOptions;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: number | null = null;
  private isConnected = false;

  constructor(url: string, options: WebSocketOptions = {}) {
    this.url = url || options.url || (import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/ws/');
    this.options = {
      reconnect: true,
      reconnectInterval: 5000,
      ...options,
    };
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        console.log('WebSocket connected');
        this.options.onConnect?.();
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.options.onMessage?.(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        console.log('WebSocket disconnected');
        this.options.onDisconnect?.();

        if (this.options.reconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectTimeout = window.setTimeout(() => {
            this.reconnectAttempts++;
            console.log(`WebSocket reconnect attempt ${this.reconnectAttempts}`);
            this.connect();
          }, this.options.reconnectInterval);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.options.onError?.(new Error('WebSocket connection error'));
      };
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      this.options.onError?.(error as Error);
    }
  }

  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }

  send(message: WebSocketMessage) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  get connected() {
    return this.isConnected;
  }
}

// Custom hook for WebSocket
export function useWebSocket(url: string, options: WebSocketOptions = {}) {
  const wsRef = useRef<WebSocketManager | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    wsRef.current = new WebSocketManager(url, {
      ...options,
      onConnect: () => {
        setIsConnected(true);
        options.onConnect?.();
      },
      onDisconnect: () => {
        setIsConnected(false);
        options.onDisconnect?.();
      },
      onError: (error) => {
        setIsConnected(false);
        options.onError?.(error);
      },
    });

    wsRef.current.connect();

    return () => {
      wsRef.current?.disconnect();
    };
  }, [url]);

  return {
    ws: wsRef.current,
    isConnected,
    send: (message: WebSocketMessage) => wsRef.current?.send(message),
  };
}

export default WebSocketManager;