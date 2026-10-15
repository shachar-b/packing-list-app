/**
 * Item & Category Dialogs (Add/Edit Item, Add/Edit Category, Reset Trip).
 */

import { api } from '../api.js';
import { store } from '../store.js';
import { modal } from './modal.js';
import { toast } from './toast.js';

const CATEGORY_EMOJIS = ['📄', '👕', '🧴', '🔌', '🎒', '🏕️', '🍳', '👟', '💊', '🏖️', '🧸', '📦'];

export function openAddItemModal(defaultCategoryId = null) {
  const trip = store.activeTrip;
  if (!trip || !trip.categories || trip.categories.length === 0) {
    toast.show('יש ליצור קודם קטגוריה ברשימה', 'warning');
    return;
  }

  const members = store.members;
  const categories = trip.categories;
  const targetCategory = defaultCategoryId || categories[0]?.id;

  const html = `
    <div class="modal-header">
      <h2 class="modal-title">➕ הוספת פריט חדש</h2>
      <button class="btn btn-icon" data-dismiss="modal">✕</button>
    </div>
    <form id="add-item-form">
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label" for="item-category">קטגוריה *</label>
          <select id="item-category" class="form-select" required>
            ${categories.map((c) => `<option value="${c.id}" ${c.id === targetCategory ? 'selected' : ''}>${c.icon} ${c.name}</option>`).join('')}
          </select>
        </div>

        <div class="form-group">
          <label class="form-label" for="item-name">שם הפריט *</label>
          <input type="text" id="item-name" class="form-input" placeholder="לדוגמה: דרכון, חולצה, מטען לטלפון" required autofocus />
        </div>

        <div class="form-group">
          <label class="form-label">כמות</label>
          <div class="stepper-container">
            <button type="button" class="stepper-btn" id="qty-minus">-</button>
            <input type="number" id="item-quantity" class="stepper-input" value="1" min="1" max="999" />
            <button type="button" class="stepper-btn" id="qty-plus">+</button>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="item-note">הערה / תזכורת (אופציונלי)</label>
          <input type="text" id="item-note" class="form-input" placeholder="לדוגמה: לבדוק תוקף, לשים בתיק היד" />
        </div>

        <div class="form-group">
          <label class="form-label">שיוך לבני משפחה</label>
          <div class="assignee-selector-grid" id="assignee-picker">
            ${members.map((m) => `
              <div class="assignee-pick-chip" data-id="${m.id}" style="background-color: ${m.color}; color: #fff;">
                <span>${m.emoji || '👤'}</span>
                <span>${m.name}</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">ביטול</button>
        <button type="submit" class="btn btn-primary">הוסף פריט</button>
      </div>
    </form>
  `;

  modal.open({
    id: 'add-item-modal',
    contentHtml: html,
    onOpen: (dialog) => {
      const selectedAssignees = new Set();
      const qtyInput = dialog.querySelector('#item-quantity');

      dialog.querySelector('#qty-minus').addEventListener('click', () => {
        const val = Math.max(1, (parseInt(qtyInput.value, 10) || 1) - 1);
        qtyInput.value = val;
      });

      dialog.querySelector('#qty-plus').addEventListener('click', () => {
        const val = Math.min(999, (parseInt(qtyInput.value, 10) || 1) + 1);
        qtyInput.value = val;
      });

      dialog.querySelectorAll('.assignee-pick-chip').forEach((chip) => {
        chip.addEventListener('click', () => {
          const id = parseInt(chip.getAttribute('data-id'), 10);
          if (selectedAssignees.has(id)) {
            selectedAssignees.delete(id);
            chip.classList.remove('selected');
          } else {
            selectedAssignees.add(id);
            chip.classList.add('selected');
          }
        });
      });

      const form = dialog.querySelector('#add-item-form');
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const categoryId = parseInt(dialog.querySelector('#item-category').value, 10);
        const name = dialog.querySelector('#item-name').value.trim();
        const quantity = parseInt(qtyInput.value, 10) || 1;
        const note = dialog.querySelector('#item-note').value.trim() || null;
        const assignee_ids = Array.from(selectedAssignees);

        if (!name) return;

        try {
          await api.createItem(categoryId, { name, quantity, note, assignee_ids });
          modal.close('add-item-modal');
          toast.show(`"${name}" נוסף בהצלחה!`, 'success');
        } catch (err) {
          toast.show(err.message || 'שגיאה בהוספת פריט', 'danger');
        }
      });
    },
  });
}

export function openEditItemModal(item) {
  const trip = store.activeTrip;
  if (!trip) return;

  const members = store.members;
  const categories = trip.categories;

  const html = `
    <div class="modal-header">
      <h2 class="modal-title">✏️ עריכת פריט</h2>
      <button class="btn btn-icon" data-dismiss="modal">✕</button>
    </div>
    <form id="edit-item-form">
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label" for="edit-item-category">קטגוריה</label>
          <select id="edit-item-category" class="form-select">
            ${categories.map((c) => `<option value="${c.id}" ${c.id === item.category_id ? 'selected' : ''}>${c.icon} ${c.name}</option>`).join('')}
          </select>
        </div>

        <div class="form-group">
          <label class="form-label" for="edit-item-name">שם הפריט *</label>
          <input type="text" id="edit-item-name" class="form-input" value="${item.name}" required autofocus />
        </div>

        <div class="form-group">
          <label class="form-label">כמות</label>
          <div class="stepper-container">
            <button type="button" class="stepper-btn" id="edit-qty-minus">-</button>
            <input type="number" id="edit-item-quantity" class="stepper-input" value="${item.quantity || 1}" min="1" max="999" />
            <button type="button" class="stepper-btn" id="edit-qty-plus">+</button>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="edit-item-note">הערה / תזכורת</label>
          <input type="text" id="edit-item-note" class="form-input" value="${item.note || ''}" placeholder="לדוגמה: לשים בתיק היד" />
        </div>

        <div class="form-group">
          <label class="form-label">שיוך לבני משפחה</label>
          <div class="assignee-selector-grid" id="edit-assignee-picker">
            ${members.map((m) => {
              const isSelected = item.assignee_ids && item.assignee_ids.includes(m.id);
              return `
                <div class="assignee-pick-chip ${isSelected ? 'selected' : ''}" data-id="${m.id}" style="background-color: ${m.color}; color: #fff;">
                  <span>${m.emoji || '👤'}</span>
                  <span>${m.name}</span>
                </div>
              `;
            }).join('')}
          </div>
        </div>

        <div style="border-top: 1px solid var(--color-border); margin-top: 1rem; padding-top: 0.75rem;">
          <button type="button" id="delete-item-btn" class="btn btn-danger-ghost" style="width: 100%; justify-content: center;">
            🗑️ מחק פריט זה
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
    id: 'edit-item-modal',
    contentHtml: html,
    onOpen: (dialog) => {
      const selectedAssignees = new Set(item.assignee_ids || []);
      const qtyInput = dialog.querySelector('#edit-item-quantity');

      dialog.querySelector('#edit-qty-minus').addEventListener('click', () => {
        const val = Math.max(1, (parseInt(qtyInput.value, 10) || 1) - 1);
        qtyInput.value = val;
      });

      dialog.querySelector('#edit-qty-plus').addEventListener('click', () => {
        const val = Math.min(999, (parseInt(qtyInput.value, 10) || 1) + 1);
        qtyInput.value = val;
      });

      dialog.querySelectorAll('.assignee-pick-chip').forEach((chip) => {
        chip.addEventListener('click', () => {
          const id = parseInt(chip.getAttribute('data-id'), 10);
          if (selectedAssignees.has(id)) {
            selectedAssignees.delete(id);
            chip.classList.remove('selected');
          } else {
            selectedAssignees.add(id);
            chip.classList.add('selected');
          }
        });
      });

      const form = dialog.querySelector('#edit-item-form');
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const category_id = parseInt(dialog.querySelector('#edit-item-category').value, 10);
        const name = dialog.querySelector('#edit-item-name').value.trim();
        const quantity = parseInt(qtyInput.value, 10) || 1;
        const note = dialog.querySelector('#edit-item-note').value.trim() || null;
        const assignee_ids = Array.from(selectedAssignees);

        if (!name) return;

        try {
          await api.updateItem(item.id, { category_id, name, quantity, note, assignee_ids });
          modal.close('edit-item-modal');
          toast.show('הפריט עודכן', 'success');
        } catch (err) {
          toast.show(err.message || 'שגיאה בעדכון פריט', 'danger');
        }
      });

      dialog.querySelector('#delete-item-btn').addEventListener('click', async () => {
        if (!confirm(`האם למחוק את "${item.name}"?`)) return;
        try {
          await api.deleteItem(item.id);
          modal.close('edit-item-modal');
          toast.show('הפריט נמחק', 'info');
        } catch (err) {
          toast.show(err.message || 'שגיאה במחיקת פריט', 'danger');
        }
      });
    },
  });
}

export function openAddCategoryModal() {
  const trip = store.activeTrip;
  if (!trip) return;

  const html = `
    <div class="modal-header">
      <h2 class="modal-title">📁 הוספת קטגוריה חדשה</h2>
      <button class="btn btn-icon" data-dismiss="modal">✕</button>
    </div>
    <form id="add-category-form">
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label" for="category-name">שם הקטגוריה *</label>
          <input type="text" id="category-name" class="form-input" placeholder="לדוגמה: ביגוד והנעלה, אלקטרוניקה" required autofocus />
        </div>

        <div class="form-group">
          <label class="form-label">אייקון / אימוג׳י</label>
          <div style="display: flex; gap: 0.5rem; align-items: center;">
            <input type="text" id="category-icon-input" class="form-input" style="width: 70px; text-align: center; font-size: 1.3rem;" value="📦" maxlength="4" />
            <div style="display: flex; gap: 4px; flex-wrap: wrap;">
              ${CATEGORY_EMOJIS.map((e) => `<button type="button" class="btn btn-secondary btn-sm cat-emoji-pick" data-emoji="${e}">${e}</button>`).join('')}
            </div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">ביטול</button>
        <button type="submit" class="btn btn-primary">צור קטגוריה</button>
      </div>
    </form>
  `;

  modal.open({
    id: 'add-category-modal',
    contentHtml: html,
    onOpen: (dialog) => {
      const iconInput = dialog.querySelector('#category-icon-input');
      dialog.querySelectorAll('.cat-emoji-pick').forEach((btn) => {
        btn.addEventListener('click', () => {
          iconInput.value = btn.getAttribute('data-emoji');
        });
      });

      const form = dialog.querySelector('#add-category-form');
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = dialog.querySelector('#category-name').value.trim();
        const icon = iconInput.value.trim() || '📦';
        if (!name) return;

        try {
          await api.createCategory(trip.id, { name, icon });
          modal.close('add-category-modal');
          toast.show('הקטגוריה נוספה בהצלחה! 📁', 'success');
        } catch (err) {
          toast.show(err.message || 'שגיאה ביצירת קטגוריה', 'danger');
        }
      });
    },
  });
}

export function openEditCategoryModal(category) {
  const html = `
    <div class="modal-header">
      <h2 class="modal-title">✏️ עריכת קטגוריה</h2>
      <button class="btn btn-icon" data-dismiss="modal">✕</button>
    </div>
    <form id="edit-category-form">
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label" for="edit-category-name">שם הקטגוריה *</label>
          <input type="text" id="edit-category-name" class="form-input" value="${category.name}" required autofocus />
        </div>

        <div class="form-group">
          <label class="form-label">אייקון / אימוג׳י</label>
          <div style="display: flex; gap: 0.5rem; align-items: center;">
            <input type="text" id="edit-category-icon" class="form-input" style="width: 70px; text-align: center; font-size: 1.3rem;" value="${category.icon || '📦'}" maxlength="4" />
            <div style="display: flex; gap: 4px; flex-wrap: wrap;">
              ${CATEGORY_EMOJIS.map((e) => `<button type="button" class="btn btn-secondary btn-sm cat-emoji-pick" data-emoji="${e}">${e}</button>`).join('')}
            </div>
          </div>
        </div>

        <div style="border-top: 1px solid var(--color-border); margin-top: 1rem; padding-top: 0.75rem;">
          <button type="button" id="delete-cat-btn" class="btn btn-danger-ghost" style="width: 100%; justify-content: center;">
            🗑️ מחק קטגוריה וכל הפריטים בה
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
    id: 'edit-category-modal',
    contentHtml: html,
    onOpen: (dialog) => {
      const iconInput = dialog.querySelector('#edit-category-icon');
      dialog.querySelectorAll('.cat-emoji-pick').forEach((btn) => {
        btn.addEventListener('click', () => {
          iconInput.value = btn.getAttribute('data-emoji');
        });
      });

      const form = dialog.querySelector('#edit-category-form');
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = dialog.querySelector('#edit-category-name').value.trim();
        const icon = iconInput.value.trim() || '📦';
        if (!name) return;

        try {
          await api.updateCategory(category.id, { name, icon });
          modal.close('edit-category-modal');
          toast.show('הקטגוריה עודכנה', 'success');
        } catch (err) {
          toast.show(err.message || 'שגיאה בעדכון קטגוריה', 'danger');
        }
      });

      dialog.querySelector('#delete-cat-btn').addEventListener('click', async () => {
        if (!confirm(`האם למחוק את הקטגוריה "${category.name}" וכל הפריטים בה?`)) return;
        try {
          await api.deleteCategory(category.id);
          modal.close('edit-category-modal');
          toast.show('הקטגוריה נמחקה', 'info');
        } catch (err) {
          toast.show(err.message || 'שגיאה במחיקת קטגוריה', 'danger');
        }
      });
    },
  });
}

export function openConfirmResetModal() {
  const trip = store.activeTrip;
  if (!trip) return;

  const html = `
    <div class="modal-header">
      <h2 class="modal-title">🔄 איפוס רשימת אריזה</h2>
      <button class="btn btn-icon" data-dismiss="modal">✕</button>
    </div>
    <div class="modal-body">
      <p style="font-size: 1rem; color: var(--color-text-main); line-height: 1.5;">
        האם לסמן את כל הפריטים ב-<strong>"${trip.name}"</strong> כלא-ארוזים?
      </p>
      <p style="font-size: 0.85rem; color: var(--color-text-muted); margin-top: 0.5rem;">
        פעולה זו מתאימה לפתיחת עונת אריזה חדשה מתוך רשימה קיימת.
      </p>
    </div>
    <div class="modal-footer">
      <button type="button" class="btn btn-secondary" data-dismiss="modal">ביטול</button>
      <button type="button" id="confirm-reset-btn" class="btn btn-danger">אפס הכל (0%)</button>
    </div>
  `;

  modal.open({
    id: 'reset-modal',
    contentHtml: html,
    onOpen: (dialog) => {
      dialog.querySelector('#confirm-reset-btn').addEventListener('click', async () => {
        try {
          await api.resetTrip(trip.id);
          modal.close('reset-modal');
          toast.show('הרשימה אופסה בהצלחה!', 'success');
        } catch (err) {
          toast.show(err.message || 'שגיאה באיפוס הרשימה', 'danger');
        }
      });
    },
  });
}
