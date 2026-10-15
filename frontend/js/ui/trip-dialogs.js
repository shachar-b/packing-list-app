/**
 * Trip Dialogs: Trip Drawer/Switcher, Create/Clone Trip, Edit Trip, WhatsApp Share.
 */

import { api } from '../api.js';
import { store } from '../store.js';
import { modal } from './modal.js';
import { toast } from './toast.js';
import { formatWhatsAppSummary, copyToClipboard, exportAllDataJson, triggerJsonImport } from '../share.js';
import { openMemberManagementModal } from './member-dialogs.js';

const COMMON_EMOJIS = ['✈️', '🏖️', '⛺', '🎿', '🚗', '🌴', '🏙️', '🎒', '🚂', '🚢', '🏕️', '🧗'];

export function openTripDrawer() {
  const currentId = store.activeTrip?.id;
  const trips = store.trips;
  const regularTrips = trips.filter((t) => !t.is_template);
  const templates = trips.filter((t) => t.is_template);

  const renderTripItem = (t) => {
    const isSelected = t.id === currentId;
    const total = t.total_items || 0;
    const packed = t.packed_items || 0;
    const pct = total === 0 ? 0 : Math.round((packed / total) * 100);

    return `
      <div class="trip-drawer-item ${isSelected ? 'active' : ''}" data-trip-id="${t.id}" style="
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.75rem 1rem; border-radius: 0.75rem; margin-bottom: 0.5rem;
        cursor: pointer; background: ${isSelected ? 'var(--color-primary-light)' : 'var(--color-surface)'};
        border: 1px solid ${isSelected ? 'var(--color-primary)' : 'var(--color-border)'};
      ">
        <div style="display: flex; align-items: center; gap: 0.75rem; min-width: 0;">
          <span style="font-size: 1.5rem; line-height: 1;">${t.emoji || '🧳'}</span>
          <div style="min-width: 0;">
            <div style="font-weight: 700; color: var(--color-text-main); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
              ${t.name}
            </div>
            <div style="font-size: 0.8rem; color: var(--color-text-muted);">
              ${t.is_template ? `${total} פריטים בתבנית` : `${packed} / ${total} נארזו (${pct}%)`}
            </div>
          </div>
        </div>
        ${isSelected ? '<span style="color: var(--color-primary); font-weight: bold; font-size: 1.1rem;">✓</span>' : ''}
      </div>
    `;
  };

  const html = `
    <div class="modal-header">
      <h2 class="modal-title">🧳 החופשות והתבניות שלי</h2>
      <button class="btn btn-icon" data-dismiss="modal" title="סגור (Esc)">✕</button>
    </div>
    <div class="modal-body" style="padding: 1rem;">
      <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem;">
        <button id="drawer-new-trip-btn" class="btn btn-primary" style="flex: 1;">+ חופשה חדשה</button>
        <button id="drawer-new-template-btn" class="btn btn-secondary" style="flex: 1;">+ תבנית חדשה</button>
      </div>

      <div style="margin-bottom: 1.5rem;">
        <h3 style="font-size: 0.95rem; font-weight: 700; color: var(--color-text-muted); margin-bottom: 0.5rem;">חופשות פעילות</h3>
        ${regularTrips.length > 0 ? regularTrips.map(renderTripItem).join('') : '<p style="font-size: 0.85rem; color: var(--color-text-subtle);">אין חופשות פעילות כרגע.</p>'}
      </div>

      <div style="margin-bottom: 1.5rem;">
        <h3 style="font-size: 0.95rem; font-weight: 700; color: var(--color-text-muted); margin-bottom: 0.5rem;">תבניות שמורות לשכפול</h3>
        ${templates.length > 0 ? templates.map(renderTripItem).join('') : '<p style="font-size: 0.85rem; color: var(--color-text-subtle);">אין תבניות שמורות.</p>'}
      </div>

      <div style="border-top: 1px solid var(--color-border); padding-top: 1rem; display: flex; flex-direction: column; gap: 0.5rem;">
        <button id="drawer-manage-members-btn" class="btn btn-secondary" style="justify-content: flex-start;">
          👥 ניהול חברי משפחה
        </button>
        <button id="drawer-export-all-btn" class="btn btn-ghost" style="justify-content: flex-start;">
          💾 גיבוי מלא לכל הנתונים (JSON)
        </button>
        <button id="drawer-import-btn" class="btn btn-ghost" style="justify-content: flex-start;">
          📥 שחזור מגיבוי (JSON)
        </button>
      </div>
    </div>
  `;

  modal.open({
    id: 'trip-drawer',
    contentHtml: html,
    isDrawer: true,
    onOpen: (dialog) => {
      // Trip selection clicks
      dialog.querySelectorAll('.trip-drawer-item').forEach((el) => {
        el.addEventListener('click', async () => {
          const tripId = parseInt(el.getAttribute('data-trip-id'), 10);
          modal.close('trip-drawer');
          await store.selectTrip(tripId);
        });
      });

      // Actions
      dialog.querySelector('#drawer-new-trip-btn').addEventListener('click', () => {
        modal.close('trip-drawer');
        openNewTripModal(false);
      });

      dialog.querySelector('#drawer-new-template-btn').addEventListener('click', () => {
        modal.close('trip-drawer');
        openNewTripModal(true);
      });

      dialog.querySelector('#drawer-manage-members-btn').addEventListener('click', () => {
        modal.close('trip-drawer');
        openMemberManagementModal();
      });

      dialog.querySelector('#drawer-export-all-btn').addEventListener('click', () => {
        exportAllDataJson();
      });

      dialog.querySelector('#drawer-import-btn').addEventListener('click', () => {
        triggerJsonImport();
      });
    },
  });
}

export function openNewTripModal(defaultIsTemplate = false) {
  const templatesAndTrips = store.trips;

  const html = `
    <div class="modal-header">
      <h2 class="modal-title">${defaultIsTemplate ? '📋 יצירת תבנית חדשה' : '✈️ יצירת חופשה חדשה'}</h2>
      <button class="btn btn-icon" data-dismiss="modal">✕</button>
    </div>
    <form id="new-trip-form">
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label" for="trip-name">שם החופשה / התבנית *</label>
          <input type="text" id="trip-name" class="form-input" placeholder="למשל: חופשת קיץ באיטליה" required autofocus />
        </div>

        <div class="form-group">
          <label class="form-label">אייקון / אימוג׳י</label>
          <div style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem;">
            <input type="text" id="trip-emoji-input" class="form-input" style="width: 70px; text-align: center; font-size: 1.3rem;" value="✈️" maxlength="4" />
            <div style="display: flex; gap: 4px; flex-wrap: wrap;">
              ${COMMON_EMOJIS.slice(0, 8).map((e) => `<button type="button" class="btn btn-secondary btn-sm emoji-quick-pick" data-emoji="${e}">${e}</button>`).join('')}
            </div>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="trip-source">התחל מרשימה קיימת (שכפול פריטים ריקים)</label>
          <select id="trip-source" class="form-select">
            <option value="">-- רשימה ריקה לגמרי --</option>
            ${templatesAndTrips.map((t) => `<option value="${t.id}">${t.is_template ? '📋 תבנית: ' : '🧳 '} ${t.name}</option>`).join('')}
          </select>
          <span class="form-hint">שכפול מעתיק את כל הקטגוריות והפריטים כשהם מסומנים כלא ארוזים.</span>
        </div>

        <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem;">
          <input type="checkbox" id="trip-is-template" style="width: 18px; height: 18px;" ${defaultIsTemplate ? 'checked' : ''} />
          <label for="trip-is-template" style="font-weight: 500; cursor: pointer;">הגדר רשימה זו כתבנית לשימוש חוזר</label>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">ביטול</button>
        <button type="submit" class="btn btn-primary">צור חופשה 🚀</button>
      </div>
    </form>
  `;

  modal.open({
    id: 'new-trip-modal',
    contentHtml: html,
    onOpen: (dialog) => {
      const emojiInput = dialog.querySelector('#trip-emoji-input');
      dialog.querySelectorAll('.emoji-quick-pick').forEach((btn) => {
        btn.addEventListener('click', () => {
          emojiInput.value = btn.getAttribute('data-emoji');
        });
      });

      const form = dialog.querySelector('#new-trip-form');
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = dialog.querySelector('#trip-name').value.trim();
        const emoji = emojiInput.value.trim() || null;
        const sourceIdVal = dialog.querySelector('#trip-source').value;
        const source_trip_id = sourceIdVal ? parseInt(sourceIdVal, 10) : null;
        const is_template = dialog.querySelector('#trip-is-template').checked;

        if (!name) return;

        try {
          const trip = await api.createTrip({ name, emoji, is_template, source_trip_id });
          modal.close('new-trip-modal');
          toast.show('חופשה נוצרה בהצלחה! 🎉', 'success');
          await store.selectTrip(trip.id);
        } catch (err) {
          toast.show(err.message || 'שגיאה ביצירת חופשה', 'danger');
        }
      });
    },
  });
}

export function openEditTripModal(trip) {
  if (!trip) return;

  const html = `
    <div class="modal-header">
      <h2 class="modal-title">✏️ עריכת חופשה / תבנית</h2>
      <button class="btn btn-icon" data-dismiss="modal">✕</button>
    </div>
    <form id="edit-trip-form">
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label" for="edit-trip-name">שם החופשה *</label>
          <input type="text" id="edit-trip-name" class="form-input" value="${trip.name}" required autofocus />
        </div>

        <div class="form-group">
          <label class="form-label">אייקון / אימוג׳י</label>
          <div style="display: flex; gap: 0.5rem; align-items: center;">
            <input type="text" id="edit-trip-emoji" class="form-input" style="width: 70px; text-align: center; font-size: 1.3rem;" value="${trip.emoji || '🧳'}" maxlength="4" />
            <div style="display: flex; gap: 4px; flex-wrap: wrap;">
              ${COMMON_EMOJIS.slice(0, 8).map((e) => `<button type="button" class="btn btn-secondary btn-sm emoji-quick-pick" data-emoji="${e}">${e}</button>`).join('')}
            </div>
          </div>
        </div>

        <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem;">
          <input type="checkbox" id="edit-trip-is-template" style="width: 18px; height: 18px;" ${trip.is_template ? 'checked' : ''} />
          <label for="edit-trip-is-template" style="font-weight: 500; cursor: pointer;">הגדר רשימה זו כתבנית לשכפול</label>
        </div>

        <div style="border-top: 1px solid var(--color-border); margin-top: 1rem; padding-top: 1rem;">
          <button type="button" id="delete-trip-btn" class="btn btn-danger-ghost" style="width: 100%; justify-content: center;">
            🗑️ מחק חופשה זו לצמיתות
          </button>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">ביטול</button>
        <button type="submit" class="btn btn-primary">שמור שינויים</button>
      </div>
    </form>
  `;

  modal.open({
    id: 'edit-trip-modal',
    contentHtml: html,
    onOpen: (dialog) => {
      const emojiInput = dialog.querySelector('#edit-trip-emoji');
      dialog.querySelectorAll('.emoji-quick-pick').forEach((btn) => {
        btn.addEventListener('click', () => {
          emojiInput.value = btn.getAttribute('data-emoji');
        });
      });

      const form = dialog.querySelector('#edit-trip-form');
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = dialog.querySelector('#edit-trip-name').value.trim();
        const emoji = emojiInput.value.trim() || null;
        const is_template = dialog.querySelector('#edit-trip-is-template').checked;

        try {
          await api.updateTrip(trip.id, { name, emoji, is_template });
          modal.close('edit-trip-modal');
          toast.show('השינויים נשמרו בהצלחה', 'success');
          await store.refreshCurrentTrip();
        } catch (err) {
          toast.show(err.message || 'שגיאה בעדכון חופשה', 'danger');
        }
      });

      dialog.querySelector('#delete-trip-btn').addEventListener('click', async () => {
        if (!confirm(`האם למחוק את "${trip.name}" לצמיתות? כל הקטגוריות והפריטים יימחקו.`)) {
          return;
        }
        try {
          await api.deleteTrip(trip.id);
          modal.close('edit-trip-modal');
          toast.show('החופשה נמחקה', 'info');
        } catch (err) {
          toast.show(err.message || 'שגיאה במחיקת חופשה', 'danger');
        }
      });
    },
  });
}

export function openWhatsAppShareModal() {
  const trip = store.activeTrip;
  if (!trip) return;

  const members = store.members;

  const html = `
    <div class="modal-header">
      <h2 class="modal-title">💬 שיתוף ב-WhatsApp</h2>
      <button class="btn btn-icon" data-dismiss="modal">✕</button>
    </div>
    <div class="modal-body">
      <div style="display: flex; gap: 1rem; margin-bottom: 0.75rem;">
        <label style="display: flex; align-items: center; gap: 0.35rem; cursor: pointer; font-weight: 600;">
          <input type="radio" name="share-mode" id="share-unpacked" checked />
          רק מה שנשאר לארוז
        </label>
        <label style="display: flex; align-items: center; gap: 0.35rem; cursor: pointer; font-weight: 600;">
          <input type="radio" name="share-mode" id="share-all" />
          רשימה מלאה (הכל)
        </label>
      </div>

      <textarea id="whatsapp-preview" class="form-textarea" rows="11" readonly style="font-family: var(--font-sans); font-size: 0.9rem; line-height: 1.4; direction: rtl;"></textarea>
    </div>
    <div class="modal-footer" style="justify-content: space-between;">
      <button type="button" class="btn btn-secondary" data-dismiss="modal">סגור</button>
      <div style="display: flex; gap: 0.5rem;">
        <button id="copy-summary-btn" class="btn btn-primary">
          📋 העתק ללוח
        </button>
        <a id="whatsapp-send-link" class="btn btn-primary" target="_blank" rel="noopener noreferrer" style="background-color: #25D366; border-color: #25D366;">
          שליחה בוואטסאפ 🚀
        </a>
      </div>
    </div>
  `;

  modal.open({
    id: 'whatsapp-share-modal',
    contentHtml: html,
    onOpen: (dialog) => {
      const preview = dialog.querySelector('#whatsapp-preview');
      const shareUnpacked = dialog.querySelector('#share-unpacked');
      const sendLink = dialog.querySelector('#whatsapp-send-link');

      const updateText = () => {
        const text = formatWhatsAppSummary(trip, members, shareUnpacked.checked);
        preview.value = text;
        sendLink.href = `https://api.whatsapp.com/send?text=${encodeURIComponent(text)}`;
      };

      shareUnpacked.addEventListener('change', updateText);
      dialog.querySelector('#share-all').addEventListener('change', updateText);
      updateText();

      dialog.querySelector('#copy-summary-btn').addEventListener('click', async () => {
        const success = await copyToClipboard(preview.value);
        if (success) {
          toast.show('הטקסט הועתק ללוח! אפשר להדביק בוואטסאפ 🎉', 'success');
          modal.close('whatsapp-share-modal');
        } else {
          toast.show('לא ניתן להעתיק אוטומטית. אנא העתק ידנית מהתיבה.', 'warning');
        }
      });
    },
  });
}
