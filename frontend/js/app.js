/**
 * Application Entry Point.
 */

import { store } from './store.js';
import { TripView } from './ui/trip-view.js';
import { toast } from './ui/toast.js';

document.addEventListener('DOMContentLoaded', async () => {
  const root = document.getElementById('app');
  new TripView(root);

  try {
    await store.init();
  } catch (err) {
    console.error('Initialization error:', err);
    toast.show('שגיאה בטעינת הנתונים מהשרת', 'danger');
  }
});
