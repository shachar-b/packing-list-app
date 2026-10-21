# Feature Backlog & Future Enhancements 🚀

This document tracks feature requests, UX improvements, and architectural ideas for future releases of the Family Vacation Packing App.

Features are **sorted by total estimated effort (Scoping/Design + Implementation/Testing)** from quickest wins to most complex. Where two features have similar effort, the one with **higher UX and Quality-of-Life (QoL) impact** is prioritized first.

---

## 📊 Prioritized Roadmap Summary

| Rank | Feature | Scoping Effort | Impl & Test Effort | UX / QoL Impact | Schema Change? |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **1** | 📋 Template "Blueprint Mode" (No Checkboxes) | Very Low | Very Low | High | No |
| **2** | 🔑 Pre-Departure House Checklist | Very Low | Very Low | High | No |
| **3** | 👥 Individual Family Member Packing Views | Very Low | Low | High | No |
| **4** | 📲 Installable PWA + Offline Asset Caching | Very Low | Low | Very High | No |
| **5** | ⚡ "Last-Minute / Morning-Of" Flag (`דקה 90`) | Low | Low–Med | Very High | Yes (`items`) |
| **6** | 🛒 "Need to Buy" Pre-Trip Status (`לקנות`) | Low–Med | Low–Med | High | Yes (`items`) |
| **7** | 🧩 Modular "Add-on Packs" (Mix & Match) | Medium | Medium | Very High | Optional |
| **8** | 🔄 "Return-Trip / Repacking Check" Mode | Medium | Medium | High | Yes (`items`) |
| **9** | 🧮 Duration / Nights Auto-Scaler | Med–High | Med–High | Med–High | Yes (`trips`/`items`) |
| **10** | 🌲 Conditional & Dependent Sub-Items | High | High | Med–High | Yes (`items`) |
| **11** | 🎒 Bag / Container Organization | High ⚠️ | High | Med–High | Yes |

---

## 1. 📋 Template "Blueprint Mode" (Disable Checkboxes & Streamline Editing)
- **Effort:** 🟢 Very Low (Scoping: Minimal | Impl & Test: ~25 mins)
- **UX / QoL Impact:** ⭐ High — Prevents accidentally packing inside a master template and makes template maintenance faster.
- **Concept:** Make templates feel unmistakably like master blueprints rather than active packing checklists.
- **Behavior:**
  - Disable/hide item checkboxes when `trip.is_template === true`.
  - Tapping anywhere on an item row in a template opens the **Edit Item** modal directly (making it much faster to tweak quantities, notes, or family tags).
  - Replace the `0%` packing progress bar, `"הסתר ארוזים"`, and `"אפס סימונים"` controls with a clean template banner and a prominent **"➕ צור נסיעה חדשה מתבנית זו"** CTA button.
  - Show simple item counts (`85 פריטים`) instead of packed ratios (`0/85`) in category headers and the trips drawer for templates.
- **Status:** Backlog — Ready to build.

---

## 2. 🔑 "Pre-Departure House Checklist" Section (סגירת הבית לפני יציאה)
- **Effort:** 🟢 Very Low (Scoping: Minimal | Impl & Test: ~30 mins)
- **UX / QoL Impact:** ⭐ High — Immediate peace of mind right before locking the front door.
- **Concept:** Final verification tasks before leaving the house (take out trash, turn off ACs & boiler, close shutters/windows, pause/run robot vacuum, lock doors).
- **Behavior:** Uses the existing category/item model (zero DB migrations). Included in default templates and available as a 1-click quick-insert button (`+ הוסף צ'ק-ליסט סגירת בית 🔑`) on any active trip.
- **Status:** Backlog — Ready to build.

---

## 3. 👥 Individual Family Member Packing Views ("My Packing Mode")
- **Effort:** 🟢 Very Low–Low (Scoping: Very Low | Impl & Test: ~45 mins)
- **UX / QoL Impact:** ⭐ High — Great when multiple family members pack in parallel or kids pack their own gear.
- **Concept:** Building on the existing member filter in `store.js`, provide a focused "My Packing Mode" toggle where a parent or child sees *only* their assigned items, empty categories are auto-collapsed, and a personal progress bar is shown (`אמא: 8/10 נארזו`).
- **Behavior:** Pure frontend UX enhancement; no backend schema changes required.
- **Status:** Backlog — Ready to build.

---

## 4. 📲 Installable PWA + Offline Asset Caching (אפליקציית מסך בית מלאה)
- **Effort:** 🟢 Low (Scoping: Very Low | Impl & Test: ~1 hour)
- **UX / QoL Impact:** 🌟 Very High — Native full-screen app feel on iOS/Android and instant cold-start even with zero reception.
- **Concept:** Pair our existing `localStorage` data cache and offline mutation queue with a Service Worker and Web App Manifest.
- **Behavior:**
  - Add `manifest.json` with RTL metadata, app icons, and `display: standalone` ("Add to Home Screen").
  - Add `sw.js` to cache static shell assets (`index.html`, CSS, JS, fonts) so the app opens from scratch even in an underground parking lot or airplane mode.
- **Status:** Backlog — Ready to build.

---

## 5. ⚡ "Last-Minute / Morning-Of" Flag (דקה 90 / בוקר היציאה)
- **Effort:** 🟡 Low–Medium (Scoping: Low | Impl & Test: ~1.5 hours)
- **UX / QoL Impact:** 🌟 Very High — Solves one of the biggest departure-morning pain points.
- **Concept:** Distinguish between items packed the night before and items that can only be packed right before walking out the door (toothbrushes, bedside chargers, chilled food/pancakes from the fridge, laptop, medications).
- **Behavior:**
  - Add `is_last_minute` boolean column to `items` (and include in export/import/cloning + seed templates).
  - Lightweight `⚡ דקה 90` toggle on items + a top filter chip so on departure morning the family sees *only* the final sweep items.
- **Status:** Backlog — Ready to build.

---

## 6. 🛒 "Need to Buy" Pre-Trip Status / Shopping Filter (להשלים בקניות)
- **Effort:** 🟡 Low–Medium (Scoping: Low–Med | Impl & Test: ~1.5 hours)
- **UX / QoL Impact:** ⭐ High — Bridges pre-trip errands and actual packing.
- **Concept:** Reviewing the packing list a few days before the trip often reveals missing or depleted items (sunscreen, mosquito spray, wine, road snacks).
- **Behavior:**
  - Add `need_to_buy` boolean flag on `items`.
  - Filter by `🛒 לקנות` while at the supermarket (and option to share just the shopping items to WhatsApp).
  - Quick 1-tap action to clear `🛒 לקנות` once purchased so it becomes a regular unpacked item.
- **Status:** Backlog — Ready to build.

---

## 7. 🧩 Modular "Add-on Packs" / Mini-Templates (Mix & Match)
- **Effort:** 🟡 Medium (Scoping: Medium | Impl & Test: ~2 hours)
- **UX / QoL Impact:** 🌟 Very High — Keeps base templates lean while making special trip variations effortless.
- **Concept:** Instead of maintaining many monolithic templates for every permutation of trip, allow injecting small modular "equipment packs" (5–10 items) into any active trip with a single click.
- **Examples:**
  - `+ הוסף ערכת חורף / גשם 🌧️`
  - `+ הוסף ערכת בריכה ומעיינות 🏊‍♂️`
  - `+ הוסף ערכת נינג'ה גריל / מנגל 🥩`
- **Behavior:** Appends the mini-template's items into matching categories of the active trip (skipping duplicates) without overwriting existing progress.
- **Status:** Backlog.

---

## 8. 🔄 "Return-Trip / Repacking Check" Mode (אריזה לחזרה הביתה)
- **Effort:** 🟡 Medium (Scoping: Medium | Impl & Test: ~2–2.5 hours)
- **UX / QoL Impact:** ⭐ High — Prevents leaving chargers in wall sockets or favorite towels at the cabin.
- **Concept:** At the end of the vacation, reset the checklist for permanent gear so you can check items off as they go back into the car, while ignoring consumables that were eaten or used.
- **Behavior:**
  - Add `is_consumable` boolean flag to `items` (pre-configured on food/disposables in templates).
  - Action button **"🔄 התארגנות לחזרה הביתה"**: unchecks all non-consumable items (and optionally hides consumables) for the return packing sweep.
- **Status:** Backlog.

---

## 9. 🧮 Duration / Nights Auto-Scaler (מחשבון כמויות לפי מספר לילות)
- **Effort:** 🟠 Medium–High (Scoping: Med–High | Impl & Test: ~2.5–3 hours)
- **UX / QoL Impact:** ⭐ Medium–High — Saves manual quantity adjustments when cloning templates for longer/shorter trips.
- **Concept:** Scale per-day items (clothes, underwear, pajamas) automatically when cloning a 2-night template into a 4-night trip, while keeping fixed gear (Ninja Grill, chargers, shampoo) at `1`.
- **Behavior:**
  - Define baseline nights on templates or a `scaling_mode` (`fixed` vs. `per_night`) on items.
  - Prompt for number of nights in the New/Clone Trip dialog and compute scaled quantities automatically.
- **Status:** Backlog.

---

## 10. 🌲 Conditional & Dependent Sub-Items (Nested Gear)
- **Effort:** 🔴 High (Scoping: High | Impl & Test: ~3.5–4 hours)
- **UX / QoL Impact:** ⭐ Medium–High (Note: much of the value can also be achieved more simply via **#7 Modular Add-on Packs**).
- **Concept:** Some packing items only have a reason to exist if their "parent" equipment is being packed (e.g., `נינג׳ה גריל` -> `מלקחיים`, `נייר אפייה מותאם לנינג'ה`, `תרסיס שמן`).
- **Behavior:** Requires parent-child item hierarchy (`parent_item_id`), nested mobile rendering, and progress calculation rules when a parent item is unchecked or omitted.
- **Status:** Backlog.

---

## 11. 🎒 Bag / Container Organization (חלוקה לתיקים / מיקום ברכב)
- **Effort:** 🔴 High (Scoping: High ⚠️ | Impl & Test: ~4+ hours)
- **UX / QoL Impact:** ⭐ Medium–High
- **Concept:** Know which bag holds which item (`🚗 תיק לאוטו`, `🏖️ תיק בריכה נגיש`, `🧊 צידנית`, `🧳 מזוודה`) so you don't unpack the entire trunk on the way north just to find swimsuits or snacks.
- **⚠️ Design Constraint (Requires Further UX Design):**
  - Adding a second set of colored tag pills next to family member assignees on every item row risks making the mobile UI visually cluttered and overwhelming.
  - **Directions to explore before implementation:**
    1. *View-Mode Switching:* Keep bags hidden during normal category view, and only show/assign them in a dedicated "Packing into Bags" view.
    2. *Sub-headers or subtle icons:* Use a single subtle icon or group-by-bag toggle rather than additional text badges on each row.
- **Status:** Needs UX/UI Design Simplification.

---

## ✅ Completed Features

### 📅 Trip Departure Date & Days-Only Countdown
- **Concept:** Attach an optional departure date to active (non-template) trips and display a clean, days-only countdown badge.
- **Implementation:**
  - Added nullable `departure_date` (`YYYY-MM-DD`) column to `trips` via migration `0002_trip_departure_date.sql` and wired through create, edit, clone, and JSON export/import.
  - Date picker in Create/Edit Trip modals (automatically hidden when `is_template` is checked, plus a quick clear button in Edit Trip).
  - Days-only countdown badge (`בעוד X ימים`, `מחר! 🎒`, `היום! 🎉`, etc.) rendered in both the main trip header and the trip drawer.
- **Status:** ✅ Completed.

### 📴 Offline Mutations Queue & Reconciliation
- **Concept:** Full offline usage (e.g., in airplane mode or spotty mobile reception).
- **Implementation:**
  - Mutations (`packed`, note edits, quantity changes) are buffered and coalesced in `localStorage` (`frontend/js/offline-queue.js`).
  - Local trip & member snapshots cached in `localStorage` for offline page reloads.
  - Sequential replay upon WebSocket reconnection with automatic state reconciliation.
- **Status:** ✅ Completed.
