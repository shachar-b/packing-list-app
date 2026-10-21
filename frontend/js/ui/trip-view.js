/**
 * Main Trip View Component.
 * Renders the header, sticky progress bar, search/filter controls, categories, and item lists.
 */

import { api } from '../api.js';
import { store, formatDepartureCountdown } from '../store.js';
import { realtime } from '../realtime.js';
import { offlineQueue } from '../offline-queue.js';
import { toast } from './toast.js';
import { openTripDrawer, openEditTripModal, openWhatsAppShareModal } from './trip-dialogs.js';
import { openAddItemModal, openEditItemModal, openAddCategoryModal, openEditCategoryModal, openConfirmResetModal } from './item-dialogs.js';

export class TripView {
  constructor(rootElement) {
    this.root = rootElement;
    this.subscribeToStore();
    this.subscribeToRealtime();
  }

  subscribeToRealtime() {
    realtime.onStatusChange((status) => {
      this.updateSyncStatus(status);
    });
    offlineQueue.onChange(() => {
      this.updateSyncStatus(realtime.status);
    });
  }

  subscribeToStore() {
    store.on('trip-changed', () => this.render());
    store.on('progress-changed', () => this.updateProgressBarOnly());
    store.on('filter-changed', () => this.renderCategoriesAndItems());
    store.on('members-changed', () => this.render());
    store.on('trips-list-changed', () => this.renderHeaderTripButton());
    store.on('trip-info-updated', () => this.renderHeaderTripButton());

    // Granular item events: update existing DOM elements when possible
    store.on('item-updated', (item) => this.handleGranularItemUpdated(item));
    store.on('item-created', () => this.renderCategoriesAndItems());
    store.on('item-deleted', () => this.renderCategoriesAndItems());
    store.on('items-changed', () => this.renderCategoriesAndItems());
    store.on('category-updated', () => this.renderCategoriesAndItems());
    store.on('category-collapse-changed', (catId) => this.toggleCategoryAccordionDom(catId));
  }

  updateSyncStatus(status) {
    const el = document.getElementById('sync-status-indicator');
    if (!el) return;

    el.className = `sync-indicator status-${status}`;
    const textEl = el.querySelector('.sync-text');
    if (textEl) {
      const pending = offlineQueue.size();
      if (offlineQueue.isFlushing) {
        textEl.textContent = 'מסנכרן שינויים... 🔄';
      } else if (pending > 0) {
        const connLabel = status === 'connected' ? 'מחובר' : 'לא מחובר';
        textEl.textContent = `${connLabel} (${pending} ממתינים לסנכרון)`;
      } else {
        if (status === 'connected') textEl.textContent = 'מחובר ומסונכרן';
        else if (status === 'reconnecting') textEl.textContent = 'מתחבר מחדש...';
        else textEl.textContent = 'לא מחובר';
      }
    }
  }

  renderHeaderTripButton() {
    const trip = store.activeTrip;
    const btn = document.getElementById('header-trip-btn');
    if (!btn) return;

    if (!trip) {
      btn.innerHTML = '<span>➕ בחר או צור חופשה</span>';
      return;
    }

    const countdown = formatDepartureCountdown(trip.departure_date, trip.is_template);
    const countdownBadge = countdown
      ? `<span class="trip-countdown-badge tone-${countdown.tone}" title="תאריך יציאה: ${countdown.formattedDate}">📅 ${countdown.text}</span>`
      : '';

    btn.innerHTML = `
      <span style="font-size: 1.4rem; line-height: 1;">${trip.emoji || '🧳'}</span>
      <span class="trip-name">${this.escape(trip.name)}</span>
      ${trip.is_template ? '<span class="trip-badge">תבנית</span>' : countdownBadge}
      <span style="font-size: 0.8rem; color: var(--color-text-subtle);">▼</span>
    `;
  }

  updateProgressBarOnly() {
    const trip = store.activeTrip;
    if (!trip) return;

    const total = trip.total_items || 0;
    const packed = trip.packed_items || 0;
    const percent = total === 0 ? 0 : Math.round((packed / total) * 100);

    const bar = document.getElementById('main-progress-bar');
    const counts = document.getElementById('main-progress-counts');
    const statusMsg = document.getElementById('main-progress-status');

    if (bar) bar.style.width = `${percent}%`;
    if (counts) counts.textContent = `${packed} / ${total} נארזו (${percent}%)`;
    if (statusMsg) statusMsg.innerHTML = this.getProgressStatusText(percent, total);

    // Also update mini category progress bars
    for (const cat of trip.categories || []) {
      const catTotal = cat.items.length;
      const catPacked = cat.items.filter((i) => i.packed).length;
      const catPct = catTotal === 0 ? 0 : Math.round((catPacked / catTotal) * 100);

      const miniBar = document.getElementById(`cat-mini-bar-${cat.id}`);
      const badge = document.getElementById(`cat-badge-${cat.id}`);
      if (miniBar) miniBar.style.width = `${catPct}%`;
      if (badge) {
        badge.textContent = `${catPacked}/${catTotal}`;
        if (catTotal > 0 && catPacked === catTotal) {
          badge.classList.add('all-packed');
        } else {
          badge.classList.remove('all-packed');
        }
      }
    }
  }

  getProgressStatusText(percent, total) {
    if (total === 0) return 'רשימת האריזה ריקה. הוסיפו פריטים למטה!';
    if (percent === 100) return '🎉 <strong>הכל ארוז! חופשה מהנה!</strong>';
    if (percent >= 75) return '💪 <strong>כמעט סיימנו! עוד קצת מאמץ...</strong>';
    if (percent >= 30) return '🎒 <strong>האריזה בעיצומה!</strong>';
    return '✈️ <strong>בואו נתחיל לארוז!</strong>';
  }

  handleGranularItemUpdated(item) {
    const row = document.getElementById(`item-row-${item.id}`);
    const currentCard = row?.closest('.category-card');
    const currentCatId = currentCard ? parseInt(currentCard.getAttribute('data-cat-id'), 10) : null;
    const hasActiveFilter =
      store.filter.status !== 'all' || store.filter.memberId !== null || Boolean(store.filter.search);

    if (!row || (item.category_id && currentCatId !== item.category_id) || hasActiveFilter) {
      this.renderCategoriesAndItems();
      this.updateProgressBarOnly();
      return;
    }

    const checkbox = row.querySelector('.checkbox-input');
    if (checkbox) checkbox.checked = item.packed;

    if (item.packed) {
      row.classList.add('is-packed');
    } else {
      row.classList.remove('is-packed');
    }

    const nameEl = row.querySelector('.item-name');
    if (nameEl) nameEl.textContent = item.name;

    const qtyEl = row.querySelector('.item-qty-badge');
    if (qtyEl) {
      if (item.quantity > 1) {
        qtyEl.textContent = `×${item.quantity}`;
        qtyEl.style.display = 'inline-block';
      } else {
        qtyEl.style.display = 'none';
      }
    }

    const noteEl = row.querySelector('.item-note');
    if (noteEl) {
      noteEl.textContent = item.note || '';
      noteEl.style.display = item.note ? 'block' : 'none';
    }

    const assigneesEl = row.querySelector('.item-assignees');
    if (assigneesEl) {
      const memberMap = new Map(store.members.map((m) => [m.id, m]));
      assigneesEl.innerHTML = (item.assignee_ids || [])
        .map((id) => memberMap.get(id))
        .filter(Boolean)
        .map((m) => `
          <span class="assignee-chip" style="background-color: ${m.color};" title="${this.escape(m.name)}">
            <span>${m.emoji || '👤'}</span>
            <span>${this.escape(m.name)}</span>
          </span>
        `).join('');
    }

    this.updateProgressBarOnly();
  }

  toggleCategoryAccordionDom(catId) {
    const card = document.getElementById(`category-card-${catId}`);
    if (card) {
      if (store.isCategoryCollapsed(catId)) {
        card.classList.add('collapsed');
      } else {
        card.classList.remove('collapsed');
      }
    }
  }

  render() {
    const trip = store.activeTrip;

    if (!trip) {
      this.renderNoTripSelected();
      return;
    }

    const total = trip.total_items || 0;
    const packed = trip.packed_items || 0;
    const percent = total === 0 ? 0 : Math.round((packed / total) * 100);

    this.root.innerHTML = `
      <!-- Header -->
      <header class="app-header">
        <div class="header-inner">
          <div class="header-title-group">
            <button id="header-trip-btn" class="trip-selector-btn touch-target" title="החלף חופשה / פתח תפריט">
              <!-- Rendered via renderHeaderTripButton() -->
            </button>
          </div>
          <div class="header-actions">
            <div id="sync-status-indicator" class="sync-indicator status-connected">
              <span class="sync-dot"></span>
              <span class="sync-text">מחובר ומסונכרן</span>
            </div>
            <button id="btn-share-whatsapp" class="btn btn-icon touch-target" title="שיתוף בוואטסאפ">
              💬
            </button>
            <button id="btn-edit-trip" class="btn btn-icon touch-target" title="הגדרות חופשה">
              ⚙️
            </button>
          </div>
        </div>

        <!-- Sticky Progress Bar Section -->
        <div class="sticky-progress-container">
          <div class="progress-header-info">
            <span id="main-progress-status" class="progress-status-msg">
              ${this.getProgressStatusText(percent, total)}
            </span>
            <span id="main-progress-counts" class="progress-counts">
              ${packed} / ${total} נארזו (${percent}%)
            </span>
          </div>
          <div class="progress-track-large" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${percent}">
            <div id="main-progress-bar" class="progress-bar-large" style="width: ${percent}%;"></div>
          </div>
        </div>
      </header>

      <!-- Toolbar & Filters -->
      <section class="toolbar-section">
        <div class="search-and-actions">
          <div class="search-input-wrapper">
            <span class="search-icon">🔍</span>
            <input type="text" id="items-search-input" class="search-input" placeholder="חיפוש פריט או הערה..." value="${this.escape(store.filter.search)}" />
            ${store.filter.search ? '<button id="clear-search-btn" class="search-clear-btn">✕</button>' : ''}
          </div>
          <button id="btn-add-category" class="btn btn-secondary touch-target" title="הוסף קטגוריה חדשה">
            + קטגוריה
          </button>
          <button id="btn-reset-trip" class="btn btn-ghost touch-target text-danger" title="איפוס כל הסימונים">
            🔄 אפס
          </button>
        </div>

        <!-- Filter Chips Row -->
        <div class="filter-chips-row">
          <button class="chip ${store.filter.status === 'all' ? 'active' : ''}" data-status="all">הכל</button>
          <button class="chip ${store.filter.status === 'unpacked' ? 'active' : ''}" data-status="unpacked">נשאר לארוז ⏳</button>
          <button class="chip ${store.filter.status === 'packed' ? 'active' : ''}" data-status="packed">נארזו ✓</button>

          <span style="width: 1px; height: 20px; background: var(--color-border); margin-inline: 4px;"></span>

          <button class="chip ${store.filter.memberId === null ? 'active' : ''}" data-member-id="null">כל המשפחה 👨‍👩‍👧‍👦</button>
          ${store.members.map((m) => `
            <button class="chip ${store.filter.memberId === m.id ? 'active' : ''}" data-member-id="${m.id}">
              <span class="chip-avatar" style="background-color: ${m.color}; color: #fff;">${m.emoji || '👤'}</span>
              <span>${m.name}</span>
            </button>
          `).join('')}
        </div>
      </section>

      <!-- Main Categories Area -->
      <main class="main-content">
        <div id="categories-container" class="categories-container">
          <!-- Categories rendered here -->
        </div>
      </main>

      <!-- Floating Action Button on Mobile -->
      <div class="fab-container">
        <button id="fab-add-item" class="fab-btn touch-target" title="הוסף פריט חדש">
          +
        </button>
      </div>
    `;

    this.renderHeaderTripButton();
    this.updateSyncStatus(realtime.status);
    this.attachHeaderAndToolbarEvents();
    this.renderCategoriesAndItems();
  }

  renderNoTripSelected() {
    this.root.innerHTML = `
      <div class="empty-state" style="margin-top: 5rem;">
        <div class="empty-state-icon">🧳</div>
        <h2 class="empty-state-title">ברוכים הבאים לאפליקציית האריזה המשפחתית!</h2>
        <p class="empty-state-desc">בחרו חופשה קיימת או צרו חופשה חדשה כדי להתחיל לארוז ביחד.</p>
        <button id="btn-create-first-trip" class="btn btn-primary" style="margin-top: 1rem;">
          + יצירת חופשה חדשה 🚀
        </button>
      </div>
    `;

    document.getElementById('btn-create-first-trip')?.addEventListener('click', () => {
      openTripDrawer();
    });
  }

  attachHeaderAndToolbarEvents() {
    // Header actions
    document.getElementById('header-trip-btn')?.addEventListener('click', () => openTripDrawer());
    document.getElementById('btn-share-whatsapp')?.addEventListener('click', () => openWhatsAppShareModal());
    document.getElementById('btn-edit-trip')?.addEventListener('click', () => openEditTripModal(store.activeTrip));
    document.getElementById('btn-add-category')?.addEventListener('click', () => openAddCategoryModal());
    document.getElementById('btn-reset-trip')?.addEventListener('click', () => openConfirmResetModal());
    document.getElementById('fab-add-item')?.addEventListener('click', () => openAddItemModal());

    // Search input
    const searchInput = document.getElementById('items-search-input');
    searchInput?.addEventListener('input', (e) => {
      store.setFilter('search', e.target.value.trim());
    });

    document.getElementById('clear-search-btn')?.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';
      store.setFilter('search', '');
    });

    // Status filter chips
    document.querySelectorAll('.filter-chips-row button[data-status]').forEach((btn) => {
      btn.addEventListener('click', () => {
        store.setFilter('status', btn.getAttribute('data-status'));
      });
    });

    // Member filter chips
    document.querySelectorAll('.filter-chips-row button[data-member-id]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const val = btn.getAttribute('data-member-id');
        store.setFilter('memberId', val === 'null' ? null : parseInt(val, 10));
      });
    });
  }

  renderCategoriesAndItems() {
    const container = document.getElementById('categories-container');
    if (!container) return;

    const trip = store.activeTrip;
    if (!trip || !trip.categories || trip.categories.length === 0) {
      container.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="empty-state-icon">📁</div>
          <h3 class="empty-state-title">עדיין אין קטגוריות ברשימה זו</h3>
          <p class="empty-state-desc">לחצו על "+ קטגוריה" כדי להתחיל לארגן את הפריטים שלכם.</p>
          <button id="empty-add-cat-btn" class="btn btn-primary btn-sm" style="margin-top: 0.5rem;">+ הוסף קטגוריה</button>
        </div>
      `;
      document.getElementById('empty-add-cat-btn')?.addEventListener('click', () => openAddCategoryModal());
      return;
    }

    const { status, memberId, search } = store.filter;
    const memberMap = new Map(store.members.map((m) => [m.id, m]));
    const searchLower = search.toLowerCase();

    let matchedAnyItem = false;

    const html = trip.categories.map((category) => {
      const isCollapsed = store.isCategoryCollapsed(category.id);
      const allItems = category.items || [];
      const catTotal = allItems.length;
      const catPacked = allItems.filter((i) => i.packed).length;
      const catPct = catTotal === 0 ? 0 : Math.round((catPacked / catTotal) * 100);

      // Filter items according to active criteria
      const filteredItems = allItems.filter((item) => {
        // Status filter
        if (status === 'unpacked' && item.packed) return false;
        if (status === 'packed' && !item.packed) return false;

        // Member filter
        if (memberId !== null && (!item.assignee_ids || !item.assignee_ids.includes(memberId))) {
          return false;
        }

        // Search filter
        if (searchLower) {
          const matchName = item.name.toLowerCase().includes(searchLower);
          const matchNote = item.note && item.note.toLowerCase().includes(searchLower);
          if (!matchName && !matchNote) return false;
        }

        return true;
      });

      if (filteredItems.length > 0) matchedAnyItem = true;

      // If search or filter is active and category has no matching items, we can dim or hide it
      const hideEmptyCategoryOnFilter = (search || status !== 'all' || memberId !== null) && filteredItems.length === 0;
      if (hideEmptyCategoryOnFilter) return '';

      return `
        <div id="category-card-${category.id}" class="category-card ${isCollapsed ? 'collapsed' : ''}" data-cat-id="${category.id}">
          <!-- Header -->
          <div class="category-header" data-cat-toggle="${category.id}">
            <div class="category-title-wrap">
              <span class="category-toggle-icon">▼</span>
              <span class="category-icon">${category.icon || '📦'}</span>
              <span class="category-name">${this.escape(category.name)}</span>
            </div>
            <div class="category-meta" onclick="event.stopPropagation();">
              <div class="category-mini-progress" title="${catPacked}/${catTotal} נארזו">
                <div id="cat-mini-bar-${category.id}" class="category-mini-bar" style="width: ${catPct}%;"></div>
              </div>
              <span id="cat-badge-${category.id}" class="category-badge ${catTotal > 0 && catPacked === catTotal ? 'all-packed' : ''}">
                ${catPacked}/${catTotal}
              </span>
              <button class="btn btn-icon btn-sm cat-edit-btn" data-cat-id="${category.id}" title="עריכת קטגוריה">
                ⋮
              </button>
            </div>
          </div>

          <!-- Content (Items list) -->
          <div class="category-content">
            <div class="items-list">
              ${filteredItems.map((item) => this.renderItemRow(item, memberMap)).join('')}
              ${filteredItems.length === 0 ? '<div style="padding: 1rem; text-align: center; color: var(--color-text-subtle); font-size: 0.85rem;">אין פריטים להצגה בקטגוריה זו</div>' : ''}
            </div>

            <!-- Inline Quick Add Input -->
            <div class="inline-add-row" onclick="event.stopPropagation();">
              <input type="text" class="inline-add-input" placeholder="+ הוסף פריט ל${this.escape(category.name)} (לחץ Enter)..." data-cat-id="${category.id}" />
            </div>
          </div>
        </div>
      `;
    }).join('');

    if (!matchedAnyItem && (search || status !== 'all' || memberId !== null)) {
      container.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <div class="empty-state-icon">🔍</div>
          <h3 class="empty-state-title">לא נמצאו פריטים תואמים לחיפוש/סינון</h3>
          <p class="empty-state-desc">נסו לשנות את מילות החיפוש או לנקות את הסינון.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = html;
    this.attachCategoryAndItemEvents(container);
  }

  renderItemRow(item, memberMap) {
    const assigneesHtml = (item.assignee_ids || [])
      .map((id) => memberMap.get(id))
      .filter(Boolean)
      .map((m) => `
        <span class="assignee-chip" style="background-color: ${m.color};" title="${m.name}">
          <span>${m.emoji || '👤'}</span>
          <span>${m.name}</span>
        </span>
      `).join('');

    return `
      <div id="item-row-${item.id}" class="item-row ${item.packed ? 'is-packed' : ''}" data-item-id="${item.id}">
        <!-- Custom Checkbox -->
        <label class="checkbox-container touch-target" title="${item.packed ? 'סמן כלא ארוז' : 'סמן כנארז'}">
          <input type="checkbox" class="checkbox-input" data-item-check="${item.id}" ${item.packed ? 'checked' : ''} />
          <span class="checkbox-custom"></span>
        </label>

        <!-- Item Info (Click to edit) -->
        <div class="item-info" data-item-edit="${item.id}">
          <div class="item-main-line">
            <span class="item-name">${this.escape(item.name)}</span>
            <span class="item-qty-badge" style="display: ${item.quantity > 1 ? 'inline-block' : 'none'};">×${item.quantity}</span>
          </div>
          <div class="item-note" style="display: ${item.note ? 'block' : 'none'};">${this.escape(item.note || '')}</div>
          <div class="item-assignees">${assigneesHtml}</div>
        </div>

        <!-- Action Edit Button -->
        <div class="item-actions">
          <button class="btn btn-icon btn-sm item-edit-btn touch-target" data-item-edit="${item.id}" title="ערוך פריט">
            ✏️
          </button>
        </div>
      </div>
    `;
  }

  attachCategoryAndItemEvents(container) {
    // Accordion toggle
    container.querySelectorAll('[data-cat-toggle]').forEach((header) => {
      header.addEventListener('click', () => {
        const catId = parseInt(header.getAttribute('data-cat-toggle'), 10);
        store.toggleCategoryCollapsed(catId);
      });
    });

    // Category options/edit
    container.querySelectorAll('.cat-edit-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const catId = parseInt(btn.getAttribute('data-cat-id'), 10);
        const cat = store.activeTrip.categories.find((c) => c.id === catId);
        if (cat) openEditCategoryModal(cat);
      });
    });

    // Inline quick add input (Enter key)
    container.querySelectorAll('.inline-add-input').forEach((input) => {
      input.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const name = input.value.trim();
          if (!name) return;

          const catId = parseInt(input.getAttribute('data-cat-id'), 10);
          input.value = '';

          try {
            await api.createItem(catId, { name, quantity: 1 });
            toast.show(`"${name}" נוסף`, 'success', 2000);
          } catch (err) {
            toast.show(err.message || 'שגיאה בהוספת פריט', 'danger');
          }
        }
      });
    });

    // Item Checkbox toggle (Optimistic & Offline-first)
    container.querySelectorAll('[data-item-check]').forEach((input) => {
      input.addEventListener('change', async () => {
        const itemId = parseInt(input.getAttribute('data-item-check'), 10);
        const checked = input.checked;

        // Optimistic UI update
        const row = document.getElementById(`item-row-${itemId}`);
        if (row) {
          if (checked) row.classList.add('is-packed');
          else row.classList.remove('is-packed');
        }

        // Optimistically update store
        for (const c of store.activeTrip.categories) {
          const item = c.items.find((i) => i.id === itemId);
          if (item) {
            item.packed = checked;
            break;
          }
        }
        store.recalculateCounts();

        try {
          const res = await offlineQueue.execute('updateItem', [itemId, { packed: checked }]);
          if (res.offline) {
            this.updateSyncStatus(realtime.status);
          }
        } catch (err) {
          // Revert on server error
          input.checked = !checked;
          if (row) {
            if (!checked) row.classList.add('is-packed');
            else row.classList.remove('is-packed');
          }
          store.refreshCurrentTrip();
          toast.show(err.message || 'שגיאה בעדכון הפריט', 'danger');
        }
      });
    });

    // Item click -> Open Edit Item Modal
    container.querySelectorAll('[data-item-edit]').forEach((el) => {
      el.addEventListener('click', (e) => {
        e.stopPropagation();
        const itemId = parseInt(el.getAttribute('data-item-edit'), 10);
        let found = null;
        for (const c of store.activeTrip.categories) {
          const item = c.items.find((i) => i.id === itemId);
          if (item) {
            found = item;
            break;
          }
        }
        if (found) {
          openEditItemModal(found);
        }
      });
    });
  }

  escape(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}
