/**
 * Application Entry Point.
 */

import { store } from './store.js';
import { TripView } from './ui/trip-view.js';
import { toast } from './ui/toast.js';

async function initApp() {
  const root = document.getElementById('app');
  if (!root) return;
  new TripView(root);

  try {
    await store.init();
  } catch (err) {
    console.error('Initialization error:', err);
    toast.show('שגיאה בטעינת הנתונים מהשרת', 'danger');
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
