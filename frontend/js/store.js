/**
 * Central Reactive Store.
 * Holds active trip, members list, filters, and applies granular real-time mutations.
 */

import { api, CLIENT_ID } from './api.js';
import { realtime } from './realtime.js';
import { offlineQueue } from './offline-queue.js';

class AppStore {
  constructor() {
    this.trips = [];
    this.activeTrip = null;
    this.members = [];
    this.filter = {
      status: 'all', // 'all' | 'unpacked' | 'packed'
      memberId: null, // null | number
      search: '',
    };
    this.collapsedCategories = new Set();
    this.listeners = new Map();

    // Listen to real-time events
    this.setupRealtimeListeners();
  }

  on(event, fn) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(fn);
    return () => this.listeners.get(event)?.delete(fn);
  }

  emit(event, data) {
    const set = this.listeners.get(event);
    if (set) {
      for (const fn of set) {
        try { fn(data); } catch (e) { console.error(e); }
      }
    }
  }

  // ------------------------------------------------------------- Storage & State
  loadCollapsedState(tripId) {
    try {
      const raw = localStorage.getItem(`packing_collapsed_${tripId}`);
      this.collapsedCategories = new Set(raw ? JSON.parse(raw) : []);
    } catch (e) {
      this.collapsedCategories = new Set();
    }
  }

  saveCollapsedState() {
    if (!this.activeTrip) return;
    try {
      localStorage.setItem(
        `packing_collapsed_${this.activeTrip.id}`,
        JSON.stringify(Array.from(this.collapsedCategories))
      );
    } catch (e) {}
  }

  toggleCategoryCollapsed(categoryId) {
    if (this.collapsedCategories.has(categoryId)) {
      this.collapsedCategories.delete(categoryId);
    } else {
      this.collapsedCategories.add(categoryId);
    }
    this.saveCollapsedState();
    this.emit('category-collapse-changed', categoryId);
  }

  isCategoryCollapsed(categoryId) {
    return this.collapsedCategories.has(categoryId);
  }

  // ------------------------------------------------------------- Initialization
  async init() {
    realtime.connect();
    offlineQueue.setOnFlushSuccess(() => this.refreshCurrentTrip());

    let trips = [];
    let members = [];

    try {
      [trips, members] = await Promise.all([
        api.getTrips(),
        api.getMembers(),
      ]);
      try {
        localStorage.setItem('packing_cache_trips', JSON.stringify(trips));
        localStorage.setItem('packing_cache_members', JSON.stringify(members));
      } catch (e) {}
    } catch (err) {
      console.warn('Network offline during init, loading cached data:', err);
      try {
        trips = JSON.parse(localStorage.getItem('packing_cache_trips')) || [];
        members = JSON.parse(localStorage.getItem('packing_cache_members')) || [];
      } catch (e) {
        trips = [];
        members = [];
      }
    }

    this.trips = trips;
    this.members = members;
    this.emit('members-changed', this.members);
    this.emit('trips-list-changed', this.trips);

    // Check URL hash for requested trip
    const hashMatch = window.location.hash.match(/trip=(\d+)/);
    const requestedTripId = hashMatch ? parseInt(hashMatch[1], 10) : null;

    let targetTripId = null;
    if (requestedTripId && trips.some((t) => t.id === requestedTripId)) {
      targetTripId = requestedTripId;
    } else if (trips.length > 0) {
      // Prefer first non-template trip, else first trip
      const nonTemplate = trips.find((t) => !t.is_template);
      targetTripId = nonTemplate ? nonTemplate.id : trips[0].id;
    }

    if (targetTripId) {
      await this.selectTrip(targetTripId, false);
    } else {
      this.emit('trip-changed', null);
    }

    // Handle browser back/forward buttons
    window.addEventListener('hashchange', () => {
      const m = window.location.hash.match(/trip=(\d+)/);
      const id = m ? parseInt(m[1], 10) : null;
      if (id && (!this.activeTrip || this.activeTrip.id !== id)) {
        this.selectTrip(id, false);
      }
    });
  }

  async refreshCurrentTrip() {
    if (!this.activeTrip) return;
    try {
      const updated = await api.getTrip(this.activeTrip.id);
      this.activeTrip = updated;
      try {
        localStorage.setItem(`packing_cache_active_trip_${this.activeTrip.id}`, JSON.stringify(updated));
      } catch (e) {}
      this.updateTripSummaryInList(updated);
      this.emit('trip-changed', this.activeTrip);
    } catch (e) {
      console.warn('Failed to refresh active trip:', e);
    }
  }

  async selectTrip(tripId, updateHash = true) {
    let trip = null;
    try {
      trip = await api.getTrip(tripId);
      try {
        localStorage.setItem(`packing_cache_active_trip_${tripId}`, JSON.stringify(trip));
      } catch (e) {}
    } catch (e) {
      console.warn('Network offline during selectTrip, checking cache:', e);
      try {
        trip = JSON.parse(localStorage.getItem(`packing_cache_active_trip_${tripId}`));
      } catch (parseErr) {}
      if (!trip) throw e;
    }

    this.activeTrip = trip;
    this.loadCollapsedState(tripId);
    if (updateHash) {
      window.location.hash = `trip=${tripId}`;
    }
    this.updateTripSummaryInList(trip);
    this.emit('trip-changed', this.activeTrip);
  }

  updateTripSummaryInList(tripData) {
    const idx = this.trips.findIndex((t) => t.id === tripData.id);
    const summary = {
      id: tripData.id,
      name: tripData.name,
      emoji: tripData.emoji,
      is_template: tripData.is_template,
      total_items: tripData.total_items ?? (tripData.categories ? tripData.categories.reduce((acc, c) => acc + c.items.length, 0) : 0),
      packed_items: tripData.packed_items ?? (tripData.categories ? tripData.categories.reduce((acc, c) => acc + c.items.filter(i => i.packed).length, 0) : 0),
      created_at: tripData.created_at,
      updated_at: tripData.updated_at,
    };

    if (idx !== -1) {
      this.trips[idx] = { ...this.trips[idx], ...summary };
    } else {
      this.trips.unshift(summary);
    }
    this.emit('trips-list-changed', this.trips);
  }

  // ----------------------------------------------------------------- Filtering
  setFilter(key, value) {
    if (this.filter[key] !== value) {
      this.filter[key] = value;
      this.emit('filter-changed', this.filter);
    }
  }

  // ------------------------------------------------------ Real-time Event Hook
  setupRealtimeListeners() {
    realtime.on('__connected__', () => {
      // When reconnected after connection drop, re-fetch active trip and members
      this.refreshCurrentTrip();
      api.getMembers().then((members) => {
        this.members = members;
        this.emit('members-changed', this.members);
      }).catch(() => {});
      api.getTrips().then((trips) => {
        this.trips = trips;
        this.emit('trips-list-changed', this.trips);
      }).catch(() => {});
    });

    // Item Events
    realtime.on('item.created', (event) => {
      if (this.activeTrip && event.trip_id === this.activeTrip.id) {
        const item = event.data;
        const cat = this.activeTrip.categories.find((c) => c.id === item.category_id);
        if (cat) {
          if (!cat.items.some((i) => i.id === item.id)) {
            cat.items.push(item);
            this.recalculateCounts();
            this.emit('item-created', { item, categoryId: cat.id });
          }
        }
      }
    });

    realtime.on('item.updated', (event) => {
      if (this.activeTrip && event.trip_id === this.activeTrip.id) {
        const updatedItem = event.data;
        let found = false;
        for (const cat of this.activeTrip.categories) {
          const idx = cat.items.findIndex((i) => i.id === updatedItem.id);
          if (idx !== -1) {
            if (updatedItem.category_id !== cat.id) {
              // Item moved to another category
              cat.items.splice(idx, 1);
              const targetCat = this.activeTrip.categories.find((c) => c.id === updatedItem.category_id);
              if (targetCat) targetCat.items.push(updatedItem);
            } else {
              cat.items[idx] = updatedItem;
            }
            found = true;
            break;
          }
        }
        if (found) {
          this.recalculateCounts();
          this.emit('item-updated', updatedItem);
        }
      }
    });

    realtime.on('item.deleted', (event) => {
      if (this.activeTrip && event.trip_id === this.activeTrip.id) {
        const { id, category_id } = event.data;
        for (const cat of this.activeTrip.categories) {
          const idx = cat.items.findIndex((i) => i.id === id);
          if (idx !== -1) {
            cat.items.splice(idx, 1);
            this.recalculateCounts();
            this.emit('item-deleted', { id, categoryId: category_id });
            break;
          }
        }
      }
    });

    // Category Events
    realtime.on('category.created', (event) => {
      if (this.activeTrip && event.trip_id === this.activeTrip.id) {
        const cat = event.data;
        if (!this.activeTrip.categories.some((c) => c.id === cat.id)) {
          this.activeTrip.categories.push({ ...cat, items: cat.items || [] });
          this.emit('trip-changed', this.activeTrip);
        }
      }
    });

    realtime.on('category.updated', (event) => {
      if (this.activeTrip && event.trip_id === this.activeTrip.id) {
        const cat = event.data;
        const idx = this.activeTrip.categories.findIndex((c) => c.id === cat.id);
        if (idx !== -1) {
          this.activeTrip.categories[idx] = {
            ...this.activeTrip.categories[idx],
            ...cat,
            items: cat.items !== undefined ? cat.items : this.activeTrip.categories[idx].items,
          };
          this.recalculateCounts();
          this.emit('category-updated', this.activeTrip.categories[idx]);
        }
      }
    });

    realtime.on('category.deleted', (event) => {
      if (this.activeTrip && event.trip_id === this.activeTrip.id) {
        const { id } = event.data;
        this.activeTrip.categories = this.activeTrip.categories.filter((c) => c.id !== id);
        this.recalculateCounts();
        this.emit('trip-changed', this.activeTrip);
      }
    });

    // Trip Events
    realtime.on('trip.snapshot', (event) => {
      if (this.activeTrip && event.trip_id === this.activeTrip.id) {
        this.activeTrip = event.data;
        this.recalculateCounts();
        this.emit('trip-changed', this.activeTrip);
      }
    });

    realtime.on('trip.created', (event) => {
      const summary = event.data;
      if (!this.trips.some((t) => t.id === summary.id)) {
        this.trips.unshift(summary);
        this.emit('trips-list-changed', this.trips);
      }
    });

    realtime.on('trip.updated', (event) => {
      const summary = event.data;
      const idx = this.trips.findIndex((t) => t.id === summary.id);
      if (idx !== -1) {
        this.trips[idx] = { ...this.trips[idx], ...summary };
        this.emit('trips-list-changed', this.trips);
      }
      if (this.activeTrip && this.activeTrip.id === summary.id) {
        this.activeTrip.name = summary.name;
        this.activeTrip.emoji = summary.emoji;
        this.activeTrip.is_template = summary.is_template;
        this.emit('trip-info-updated', this.activeTrip);
      }
    });

    realtime.on('trip.deleted', (event) => {
      const { id } = event.data;
      this.trips = this.trips.filter((t) => t.id !== id);
      this.emit('trips-list-changed', this.trips);
      if (this.activeTrip && this.activeTrip.id === id) {
        const next = this.trips[0];
        if (next) {
          this.selectTrip(next.id);
        } else {
          this.activeTrip = null;
          this.emit('trip-changed', null);
        }
      }
    });

    // Member Events
    realtime.on('member.created', (event) => {
      const member = event.data;
      if (!this.members.some((m) => m.id === member.id)) {
        this.members.push(member);
        this.emit('members-changed', this.members);
      }
    });

    realtime.on('member.updated', (event) => {
      const member = event.data;
      const idx = this.members.findIndex((m) => m.id === member.id);
      if (idx !== -1) {
        this.members[idx] = member;
        this.emit('members-changed', this.members);
      }
    });

    realtime.on('member.deleted', (event) => {
      const { id } = event.data;
      this.members = this.members.filter((m) => m.id !== id);
      this.emit('members-changed', this.members);
      // Remove assignment from active trip if present
      if (this.activeTrip) {
        for (const cat of this.activeTrip.categories) {
          for (const item of cat.items) {
            item.assignee_ids = item.assignee_ids.filter((mId) => mId !== id);
          }
        }
        this.emit('items-changed');
      }
    });
  }

  recalculateCounts() {
    if (!this.activeTrip) return;
    let total = 0;
    let packed = 0;
    for (const c of this.activeTrip.categories) {
      for (const i of c.items) {
        total++;
        if (i.packed) packed++;
      }
    }
    this.activeTrip.total_items = total;
    this.activeTrip.packed_items = packed;
    this.updateTripSummaryInList(this.activeTrip);
    this.emit('progress-changed', { total, packed, percent: total === 0 ? 0 : Math.round((packed / total) * 100) });
  }
}

export const store = new AppStore();
