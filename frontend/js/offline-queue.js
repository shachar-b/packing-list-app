/**
 * Offline Mutation Queue and Conflict Resolution.
 * Buffers mutations in localStorage when offline or disconnected.
 * Replays them sequentially upon reconnection and refreshes the reactive store.
 */

import { api } from './api.js';
import { realtime } from './realtime.js';
import { toast } from './ui/toast.js';

const QUEUE_STORAGE_KEY = 'packing_offline_queue_v1';

class OfflineMutationQueue {
  constructor() {
    this.queue = this.loadQueue();
    this.isFlushing = false;
    this.listeners = new Set();
    this.onFlushSuccess = null;

    // Flush automatically when WebSocket reconnects or browser comes online
    realtime.on('__connected__', () => {
      this.flush();
    });

    window.addEventListener('online', () => {
      this.flush();
    });
  }

  setOnFlushSuccess(cb) {
    this.onFlushSuccess = cb;
  }

  loadQueue() {
    try {
      const raw = localStorage.getItem(QUEUE_STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      console.warn('Failed to load offline queue from storage:', e);
      return [];
    }
  }

  saveQueue() {
    try {
      localStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(this.queue));
    } catch (e) {
      console.error('Failed to save offline queue to storage:', e);
    }
    this.notify();
  }

  onChange(fn) {
    this.listeners.add(fn);
    fn(this.size());
    return () => this.listeners.delete(fn);
  }

  notify() {
    const s = this.size();
    for (const fn of this.listeners) {
      try {
        fn(s);
      } catch (e) {
        console.error(e);
      }
    }
  }

  size() {
    return this.queue.length;
  }

  /**
   * Enqueue a mutation.
   * If an update for the same item already exists in the queue, coalesce them into a single record.
   */
  enqueue(action, params) {
    const timestamp = Date.now();

    if (action === 'updateItem') {
      const [itemId, changes] = params;
      const existingIdx = this.queue.findIndex(
        (entry) => entry.action === 'updateItem' && entry.params[0] === itemId
      );

      if (existingIdx !== -1) {
        // Coalesce changes for the same item
        const existing = this.queue[existingIdx];
        existing.params[1] = { ...existing.params[1], ...changes };
        existing.timestamp = timestamp;
        this.saveQueue();
        return;
      }
    }

    this.queue.push({
      id: 'mut_' + Math.random().toString(36).substring(2, 9),
      action,
      params,
      timestamp,
    });

    this.saveQueue();
  }

  /**
   * Attempt to execute an operation. If offline or network fails, enqueue it instead of throwing.
   */
  async execute(action, params) {
    const isOnline = navigator.onLine !== false && realtime.status === 'connected';

    if (!isOnline) {
      this.enqueue(action, params);
      return { offline: true };
    }

    try {
      const res = await api[action](...params);
      return { offline: false, result: res };
    } catch (err) {
      const isNetworkError =
        !err.status ||
        err.message?.includes('fetch') ||
        err.message?.includes('Network') ||
        err.message?.includes('Failed to fetch');

      if (isNetworkError) {
        this.enqueue(action, params);
        return { offline: true };
      }
      throw err;
    }
  }

  /**
   * Flush all queued mutations sequentially to the server.
   */
  async flush() {
    if (this.isFlushing || this.queue.length === 0) return;
    if (navigator.onLine === false) return;

    this.isFlushing = true;
    this.notify();

    let itemsProcessed = 0;

    try {
      while (this.queue.length > 0) {
        const item = this.queue[0];
        try {
          if (typeof api[item.action] === 'function') {
            await api[item.action](...item.params);
          }
          // Successfully executed, remove from queue
          this.queue.shift();
          this.saveQueue();
          itemsProcessed++;
        } catch (err) {
          // If item was deleted on the server (404), drop it and continue
          if (err.status === 404) {
            this.queue.shift();
            this.saveQueue();
            continue;
          }

          // If connection dropped again, stop flushing and wait for reconnect
          const isNetworkError =
            !err.status ||
            err.message?.includes('fetch') ||
            err.message?.includes('Network') ||
            err.message?.includes('Failed to fetch');

          if (isNetworkError) {
            console.warn('Network offline during flush, pausing queue:', err);
            break;
          }

          // Non-network error (e.g. 400 validation): drop to prevent permanently blocked queue
          console.error('Dropping unprocessable mutation:', item, err);
          this.queue.shift();
          this.saveQueue();
        }
      }
    } finally {
      this.isFlushing = false;
      this.notify();

      if (itemsProcessed > 0) {
        toast.show(`סונכרנו ${itemsProcessed} שינויים שבוצעו במצב לא מקוון ☁️`, 'success', 3000);
        if (typeof this.onFlushSuccess === 'function') {
          this.onFlushSuccess();
        }
      }
    }
  }
}

export const offlineQueue = new OfflineMutationQueue();
