/**
 * WebSocket real-time synchronization client.
 * Manages heartbeats, automatic reconnection, and event dispatching.
 */

import { CLIENT_ID } from './api.js';

class RealtimeClient {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectDelay = 10000;
    this.pingIntervalId = null;
    this.statusListeners = new Set();
    this.eventListeners = new Map();
    this.status = 'disconnected'; // 'connected' | 'reconnecting' | 'offline'
    this.intentionalClose = false;

    // Handle mobile screen wake / tab focus
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
          this.reconnect(true);
        }
      }
    });

    window.addEventListener('online', () => this.reconnect(true));
    window.addEventListener('offline', () => this.setStatus('offline'));
  }

  onStatusChange(fn) {
    this.statusListeners.add(fn);
    fn(this.status);
    return () => this.statusListeners.delete(fn);
  }

  on(eventType, fn) {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, new Set());
    }
    this.eventListeners.get(eventType).add(fn);
    return () => this.eventListeners.get(eventType)?.delete(fn);
  }

  setStatus(newStatus) {
    if (this.status !== newStatus) {
      this.status = newStatus;
      for (const fn of this.statusListeners) {
        try { fn(this.status); } catch (e) { console.error(e); }
      }
    }
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws?client_id=${encodeURIComponent(CLIENT_ID)}`;

    try {
      this.ws = new WebSocket(wsUrl);
    } catch (e) {
      console.warn('WebSocket init failed:', e);
      this.scheduleReconnect();
      return;
    }

    this.setStatus(this.reconnectAttempts === 0 ? 'reconnecting' : 'reconnecting');

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.setStatus('connected');
      this.startHeartbeat();
      // Notify listeners of reconnection so they can refresh stale data
      this.dispatch({ type: '__connected__' });
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'pong' || msg.type === 'hello') {
          return;
        }
        this.dispatch(msg);
      } catch (e) {
        console.error('Failed to parse WS message:', e);
      }
    };

    this.ws.onclose = () => {
      this.stopHeartbeat();
      if (!this.intentionalClose) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (err) => {
      console.warn('WebSocket error:', err);
      // onclose will follow
    };
  }

  reconnect(immediate = false) {
    if (this.ws) {
      try { this.ws.close(); } catch (e) {}
    }
    if (immediate) {
      this.reconnectAttempts = 0;
      this.connect();
    } else {
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    this.setStatus(navigator.onLine === false ? 'offline' : 'reconnecting');
    const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), this.maxReconnectDelay);
    this.reconnectAttempts++;
    setTimeout(() => {
      if (!this.intentionalClose) {
        this.connect();
      }
    }, delay);
  }

  startHeartbeat() {
    this.stopHeartbeat();
    this.pingIntervalId = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping', ts: Date.now() }));
      }
    }, 20000);
  }

  stopHeartbeat() {
    if (this.pingIntervalId) {
      clearInterval(this.pingIntervalId);
      this.pingIntervalId = null;
    }
  }

  dispatch(event) {
    const listeners = this.eventListeners.get(event.type);
    if (listeners) {
      for (const fn of listeners) {
        try { fn(event); } catch (e) { console.error(e); }
      }
    }
    // Wildcard listeners
    const all = this.eventListeners.get('*');
    if (all) {
      for (const fn of all) {
        try { fn(event); } catch (e) { console.error(e); }
      }
    }
  }
}

export const realtime = new RealtimeClient();
