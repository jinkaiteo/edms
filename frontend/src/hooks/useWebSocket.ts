/**
 * Custom hook for WebSocket connections
 * 
 * Provides real-time WebSocket communication with automatic reconnection,
 * connection state management, and message handling.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

interface UseWebSocketOptions {
  url: string;
  protocols?: string | string[];
  onOpen?: (event: Event) => void;
  onMessage?: (event: MessageEvent) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  shouldReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  enabled?: boolean;
}

interface UseWebSocketReturn {
  socket: WebSocket | null;
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastMessage: MessageEvent | null;
  sendMessage: (message: string | ArrayBuffer | Blob) => boolean;
  connect: () => void;
  disconnect: () => void;
  reconnectAttempts: number;
  isReconnecting: boolean;
}

export const useWebSocket = ({
  url,
  protocols,
  onOpen,
  onMessage,
  onClose,
  onError,
  shouldReconnect = true,
  reconnectInterval = 3000,
  maxReconnectAttempts = 5,
  enabled = true
}: UseWebSocketOptions): UseWebSocketReturn => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [isReconnecting, setIsReconnecting] = useState(false);
  
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(shouldReconnect);
  const enabledRef = useRef(enabled);
  
  // Update refs when props change
  useEffect(() => {
    shouldReconnectRef.current = shouldReconnect;
    enabledRef.current = enabled;
  }, [shouldReconnect, enabled]);
  
  // Send message through WebSocket
  const sendMessage = useCallback((message: string | ArrayBuffer | Blob): boolean => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      try {
        socket.send(message);
        return true;
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
        return false;
      }
    }
    return false;
  }, [socket]);
  
  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!enabledRef.current) return;
    
    try {
      console.log('🔗 Connecting to WebSocket:', url);
      setConnectionState('connecting');
      
      const newSocket = new WebSocket(url, protocols);
      
      newSocket.onopen = (event) => {
        console.log('✅ WebSocket connected');
        setConnectionState('connected');
        setReconnectAttempts(0);
        setIsReconnecting(false);
        onOpen?.(event);
      };
      
      newSocket.onmessage = (event) => {
        setLastMessage(event);
        onMessage?.(event);
      };
      
      newSocket.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason);
        setConnectionState('disconnected');
        setSocket(null);
        onClose?.(event);
        
        // Attempt to reconnect if enabled and not a normal closure
        if (shouldReconnectRef.current && event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
          setIsReconnecting(true);
          setReconnectAttempts(prev => prev + 1);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`🔄 Reconnecting... (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`);
            connect();
          }, reconnectInterval);
        }
      };
      
      newSocket.onerror = (event) => {
        console.error('❌ WebSocket error:', event);
        setConnectionState('error');
        onError?.(event);
      };
      
      setSocket(newSocket);
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionState('error');
    }
  }, [url, protocols, onOpen, onMessage, onClose, onError, reconnectAttempts, maxReconnectAttempts, reconnectInterval]);
  
  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (socket) {
      socket.close(1000, 'Intentional disconnect');
    }
    
    setSocket(null);
    setConnectionState('disconnected');
    setIsReconnecting(false);
    setReconnectAttempts(0);
  }, [socket]);
  
  // Initial connection and cleanup
  useEffect(() => {
    if (enabled) {
      connect();
    }
    
    return () => {
      disconnect();
    };
  }, [enabled, url, protocols]); // Only reconnect when URL or protocols change
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);
  
  return {
    socket,
    connectionState,
    lastMessage,
    sendMessage,
    connect,
    disconnect,
    reconnectAttempts,
    isReconnecting
  };
};