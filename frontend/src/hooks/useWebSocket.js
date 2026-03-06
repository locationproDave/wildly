import { useState, useEffect, useCallback, useRef } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const useWebSocket = (channel = 'admin') => {
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    try {
      // Convert HTTP URL to WebSocket URL
      const wsUrl = BACKEND_URL
        .replace('https://', 'wss://')
        .replace('http://', 'ws://');
      
      const ws = new WebSocket(`${wsUrl}/ws/${channel}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          setNotifications(prev => [data, ...prev].slice(0, 50)); // Keep last 50
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // Try to reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }, [channel]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
    }
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected,
    notifications,
    lastMessage,
    clearNotifications
  };
};

export const NotificationType = {
  NEW_ORDER: 'new_order',
  ORDER_UPDATE: 'order_update',
  LOW_STOCK: 'low_stock',
  NEW_CUSTOMER: 'new_customer',
  NEW_REVIEW: 'new_review',
  REVENUE_UPDATE: 'revenue_update'
};

export default useWebSocket;
