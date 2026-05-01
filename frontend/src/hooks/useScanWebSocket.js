/**
 * useScanWebSocket.js - React hook for scan WebSocket connection.
 *
 * Features:
 * - Auto-reconnect with exponential backoff
 * - Message type routing (phase, model, finding, tool)
 * - Heartbeat ping/pong
 * - Connection state management
 */

import { useState, useEffect, useRef, useCallback } from 'react';

const configuredBackendBaseUrl =
  process.env.VITE_API_BASE_URL === '/api/v1' ? '' : process.env.VITE_API_BASE_URL;

function resolveWebSocketBaseUrl() {
  const baseUrl =
    configuredBackendBaseUrl ||
    (typeof window === 'undefined' ? 'http://localhost:8000' : `http://${window.location.hostname}:8000`);
  return baseUrl.replace(/\/+$/, '').replace(/^http:/, 'ws:').replace(/^https:/, 'wss:');
}

const WS_STATES = {
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3,
};

const useScanWebSocket = (scanId, options = {}) => {
  const {
    onMessage,
    onPhaseUpdate,
    onModelActivity,
    onFinding,
    onToolLog,
    onConnect,
    onDisconnect,
    onError,
    reconnectInterval = 1000,
    maxReconnectAttempts = 10,
    heartbeatInterval = 30000,
  } = options;

  const [readyState, setReadyState] = useState(WS_STATES.CLOSED);
  const [lastMessage, setLastMessage] = useState(null);
  const [reconnectCount, setReconnectCount] = useState(0);

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const heartbeatIntervalRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const isManualCloseRef = useRef(false);

  const getWsUrl = useCallback(() => {
    return `${resolveWebSocketBaseUrl()}/ws/scan/${scanId}`;
  }, [scanId]);

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const clearHeartbeatInterval = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  const startHeartbeat = useCallback(() => {
    clearHeartbeatInterval();
    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WS_STATES.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, heartbeatInterval);
  }, [heartbeatInterval]);

  const handleMessage = useCallback(
    (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);

        // Call general message handler
        onMessage?.(data);

        // Route by message type
        switch (data.type) {
          case 'phase_update':
            onPhaseUpdate?.(data.data);
            break;
          case 'model_activity':
            onModelActivity?.(data.data);
            break;
          case 'finding':
            onFinding?.(data.data);
            break;
          case 'tool_log':
            onToolLog?.(data.data);
            break;
          case 'log':
            // Agent log messages
            if (data.data.model_role) {
              onModelActivity?.(data.data);
            } else {
              onToolLog?.(data.data);
            }
            break;
          case 'pong':
            // Heartbeat response, no action needed
            break;
          default:
            break;
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    },
    [onMessage, onPhaseUpdate, onModelActivity, onFinding, onToolLog]
  );

  const connect = useCallback(() => {
    if (!scanId || wsRef.current?.readyState === WS_STATES.OPEN) {
      return;
    }

    isManualCloseRef.current = false;
    setReadyState(WS_STATES.CONNECTING);

    try {
      const ws = new WebSocket(getWsUrl());
      wsRef.current = ws;

      ws.onopen = () => {
        setReadyState(WS_STATES.OPEN);
        reconnectAttemptsRef.current = 0;
        setReconnectCount(0);
        startHeartbeat();
        onConnect?.();
      };

      ws.onmessage = handleMessage;

      ws.onclose = (event) => {
        setReadyState(WS_STATES.CLOSED);
        clearHeartbeatInterval();

        if (!isManualCloseRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(
            reconnectInterval * Math.pow(2, reconnectAttemptsRef.current),
            30000 // Max 30s delay
          );

          reconnectAttemptsRef.current += 1;
          setReconnectCount(reconnectAttemptsRef.current);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        }

        onDisconnect?.(event);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      onError?.(err);
    }
  }, [
    scanId,
    getWsUrl,
    handleMessage,
    startHeartbeat,
    onConnect,
    onDisconnect,
    onError,
    reconnectInterval,
    maxReconnectAttempts,
  ]);

  const disconnect = useCallback(() => {
    isManualCloseRef.current = true;
    clearReconnectTimeout();
    clearHeartbeatInterval();

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setReadyState(WS_STATES.CLOSED);
  }, []);

  const sendMessage = useCallback((data) => {
    if (wsRef.current?.readyState === WS_STATES.OPEN) {
      wsRef.current.send(JSON.stringify(data));
      return true;
    }
    return false;
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    readyState,
    readyStateLabel: ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'][readyState],
    lastMessage,
    reconnectCount,
    connect,
    disconnect,
    sendMessage,
    isConnected: readyState === WS_STATES.OPEN,
  };
};

export default useScanWebSocket;
