/**
 * Sharing, plain-text export for WhatsApp, and JSON backup/restore.
 */

import { api } from './api.js';
import { store } from './store.js';
import { toast } from './ui/toast.js';

export function formatWhatsAppSummary(trip, members, onlyUnpacked = false) {
  if (!trip) return '';

  const memberMap = new Map(members.map((m) => [m.id, m.name]));
  const total = trip.total_items || 0;
  const packed = trip.packed_items || 0;
  const percent = total === 0 ? 0 : Math.round((packed / total) * 100);

  const lines = [];
  const emoji = trip.emoji ? `${trip.emoji} ` : '🧳 ';
  lines.push(`${emoji}*${trip.name}*`);

  if (onlyUnpacked) {
    const remaining = total - packed;
    lines.push(`📝 *נשאר לארוז: ${remaining} מתוך ${total} פריטים*`);
  } else {
    lines.push(`📊 *מצב אריזה: ${packed} מתוך ${total} נארזו (${percent}%)*`);
  }
  lines.push('');

  let totalIncluded = 0;

  for (const cat of trip.categories || []) {
    const relevantItems = cat.items.filter((item) => (onlyUnpacked ? !item.packed : true));
    if (relevantItems.length === 0) continue;

    const catIcon = cat.icon ? `${cat.icon} ` : '📦 ';
    lines.push(`${catIcon}*${cat.name}*`);

    for (const item of relevantItems) {
      totalIncluded++;
      const check = item.packed ? '✅' : '⬜';
      const qty = item.quantity > 1 ? ` (×${item.quantity})` : '';
      const note = item.note ? ` - _${item.note}_` : '';
      const assignees = item.assignee_ids && item.assignee_ids.length > 0
        ? ` [${item.assignee_ids.map((id) => memberMap.get(id) || '').filter(Boolean).join(', ')}]`
        : '';

      lines.push(`${check} ${item.name}${qty}${note}${assignees}`);
    }
    lines.push('');
  }

  if (totalIncluded === 0) {
    if (onlyUnpacked) {
      lines.push('🎉 *הכל ארוז! אין פריטים שנשארו לארוז.*');
    } else {
      lines.push('אין פריטים ברשימה זו.');
    }
    lines.push('');
  }

  lines.push('נשלח מאפליקציית האריזה המשפחתית 🎒');
  return lines.join('\n');
}

export async function copyToClipboard(text) {
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch (err) {}

  // Fallback for mobile / browsers without clipboard permission
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  try {
    const successful = document.execCommand('copy');
    document.body.removeChild(textarea);
    return successful;
  } catch (err) {
    document.body.removeChild(textarea);
    return false;
  }
}

export function downloadJson(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function exportCurrentTripJson() {
  const trip = store.activeTrip;
  if (!trip) return;
  try {
    const res = await fetch(api.exportTripUrl(trip.id));
    if (!res.ok) throw new Error('ייצוא נכשל');
    const doc = await res.json();
    const cleanName = trip.name.replace(/[^a-zA-Z0-9א-ת_-]/g, '_');
    downloadJson(doc, `packing_${cleanName}.json`);
    toast.show('הקובץ הורד בהצלחה 💾', 'success');
  } catch (e) {
    toast.show(e.message || 'שגיאה בהורדת הקובץ', 'danger');
  }
}

export async function exportAllDataJson() {
  try {
    const res = await fetch(api.exportAllUrl());
    if (!res.ok) throw new Error('גיבוי מלא נכשל');
    const doc = await res.json();
    const date = new Date().toISOString().slice(0, 10);
    downloadJson(doc, `family_packing_backup_${date}.json`);
    toast.show('גיבוי מלא הורד בהצלחה 💾', 'success');
  } catch (e) {
    toast.show(e.message || 'שגיאה בהורדת הגיבוי', 'danger');
  }
}

export async function processImportDocument(doc) {
  if (!doc || doc.format !== 'family-packing-list') {
    throw new Error('מבנה נתונים לא תקין. יש לוודא שהפורמט הוא family-packing-list.');
  }

  const res = await api.importData(doc);
  const tripCount = res.trips?.length || 0;
  const tripName = res.trips && res.trips[0] ? res.trips[0].name : '';

  if (tripCount === 1) {
    toast.show(`החופשה "${tripName}" יובאה בהצלחה! 🎉`, 'success');
  } else {
    toast.show(`יובאו בהצלחה ${tripCount} חופשות ו-${res.members_created} חברי משפחה! 🎉`, 'success');
  }

  // Refresh store and select newly imported trip
  await store.init();
  if (res.trips && res.trips.length > 0) {
    await store.selectTrip(res.trips[0].id);
  }
  return res;
}

export function triggerJsonImport() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.json,application/json';
  input.style.display = 'none';

  input.onchange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      const text = await file.text();
      const doc = JSON.parse(text);
      await processImportDocument(doc);
    } catch (err) {
      console.error(err);
      toast.show(err.message || 'שגיאה בקריאת הקובץ', 'danger');
    }
  };

  document.body.appendChild(input);
  input.click();
  document.body.removeChild(input);
}
