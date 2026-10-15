/**
 * Family Member Management Dialog.
 */

import { api } from '../api.js';
import { store } from '../store.js';
import { modal } from './modal.js';
import { toast } from './toast.js';

const PRESET_COLORS = ['#6366f1', '#0ea5e9', '#10b981', '#ec4899', '#f59e0b', '#8b5cf6', '#ef4444', '#14b8a6'];
const PRESET_EMOJIS = ['👨‍👩‍👧‍👦', '🧑‍🤝‍🧑', '👨', '👩', '🧒', '👶', '👵', '👴', '🐶', '🐱'];

export function openMemberManagementModal() {
  const members = store.members;

  const renderMemberList = () => {
    if (store.members.length === 0) {
      return '<p style="color: var(--color-text-muted); font-size: 0.9rem;">לא הוגדרו עדיין בני משפחה.</p>';
    }

    return store.members.map((m) => `
      <div class="member-row" style="
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.6rem 0.8rem; border-radius: var(--radius-lg); background: var(--color-surface);
        border: 1px solid var(--color-border); margin-bottom: 0.5rem;
      ">
        <div style="display: flex; align-items: center; gap: 0.6rem;">
          <span style="
            width: 32px; height: 32px; border-radius: 50%; background-color: ${m.color};
            display: inline-flex; align-items: center; justify-content: center;
            font-size: 1.1rem; color: #fff; box-shadow: var(--shadow-xs);
          ">${m.emoji || '👤'}</span>
          <span style="font-weight: 600; color: var(--color-text-main);">${m.name}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 4px;">
          <button class="btn btn-icon btn-sm delete-member-btn" data-id="${m.id}" data-name="${m.name}" title="מחק">🗑️</button>
        </div>
      </div>
    `).join('');
  };

  const html = `
    <div class="modal-header">
      <h2 class="modal-title">👥 ניהול חברי משפחה</h2>
      <button class="btn btn-icon" data-dismiss="modal">✕</button>
    </div>
    <div class="modal-body">
      <!-- Add Member Form -->
      <form id="add-member-form" style="background: var(--color-surface-sunken); padding: 0.85rem; border-radius: var(--radius-xl); border: 1px solid var(--color-border);">
        <h3 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 0.5rem;">+ הוספת בן / בת משפחה</h3>
        <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
          <input type="text" id="new-member-name" class="form-input" placeholder="שם (לדוגמה: אבא, רוני, סבתא)" required style="flex: 1;" />
          <input type="text" id="new-member-emoji" class="form-input" value="👤" maxlength="4" style="width: 55px; text-align: center; font-size: 1.2rem;" />
        </div>

        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
          <!-- Color Picker Pills -->
          <div style="display: flex; gap: 6px; align-items: center;">
            <span style="font-size: 0.8rem; color: var(--color-text-muted);">צבע:</span>
            <input type="hidden" id="new-member-color" value="#6366f1" />
            <div id="color-presets" style="display: flex; gap: 5px;">
              ${PRESET_COLORS.map((c, i) => `
                <button type="button" class="color-dot ${i === 0 ? 'selected' : ''}" data-color="${c}" style="
                  width: 22px; height: 22px; border-radius: 50%; background-color: ${c};
                  border: 2px solid ${i === 0 ? 'var(--color-text-main)' : 'transparent'}; cursor: pointer;
                "></button>
              `).join('')}
            </div>
          </div>

          <button type="submit" class="btn btn-primary btn-sm">הוסף למשפחה</button>
        </div>
      </form>

      <!-- Member List -->
      <div style="margin-top: 1rem;">
        <h3 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 0.5rem;">בני המשפחה הרשומים</h3>
        <div id="members-list-container">
          ${renderMemberList()}
        </div>
      </div>
    </div>
    <div class="modal-footer">
      <button type="button" class="btn btn-primary" data-dismiss="modal">סיום</button>
    </div>
  `;

  modal.open({
    id: 'members-modal',
    contentHtml: html,
    onOpen: (dialog) => {
      const form = dialog.querySelector('#add-member-form');
      const nameInput = dialog.querySelector('#new-member-name');
      const emojiInput = dialog.querySelector('#new-member-emoji');
      const colorInput = dialog.querySelector('#new-member-color');
      const listContainer = dialog.querySelector('#members-list-container');

      // Color selection
      dialog.querySelectorAll('.color-dot').forEach((btn) => {
        btn.addEventListener('click', () => {
          dialog.querySelectorAll('.color-dot').forEach((b) => b.style.borderColor = 'transparent');
          btn.style.borderColor = 'var(--color-text-main)';
          colorInput.value = btn.getAttribute('data-color');
        });
      });

      // Submit new member
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = nameInput.value.trim();
        const emoji = emojiInput.value.trim() || null;
        const color = colorInput.value || '#6366f1';

        if (!name) return;

        try {
          await api.createMember({ name, color, emoji });
          nameInput.value = '';
          toast.show(`${name} נוסף/ה בהצלחה!`, 'success');
          // Update store members
          const updated = await api.getMembers();
          store.members = updated;
          listContainer.innerHTML = renderMemberList();
          attachDeleteHandlers();
        } catch (err) {
          toast.show(err.message || 'שגיאה בהוספת חבר משפחה', 'danger');
        }
      });

      const attachDeleteHandlers = () => {
        listContainer.querySelectorAll('.delete-member-btn').forEach((btn) => {
          btn.addEventListener('click', async () => {
            const id = parseInt(btn.getAttribute('data-id'), 10);
            const name = btn.getAttribute('data-name');
            if (!confirm(`האם למחוק את "${name}"? שיוכים לפריטים יוסרו.`)) return;

            try {
              await api.deleteMember(id);
              toast.show(`${name} הוסר/ה`, 'info');
              const updated = await api.getMembers();
              store.members = updated;
              listContainer.innerHTML = renderMemberList();
              attachDeleteHandlers();
            } catch (err) {
              toast.show(err.message || 'שגיאה במחיקה', 'danger');
            }
          });
        });
      };

      attachDeleteHandlers();
    },
  });
}
