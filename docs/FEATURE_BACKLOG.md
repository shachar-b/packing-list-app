# Feature Backlog & Future Enhancements 🚀

This document tracks feature requests, UX improvements, and architectural ideas for future releases of the Family Vacation Packing App.

---

## 1. 🌲 Conditional & Dependent Sub-Items (Nested Gear)
- **Concept:** Some packing items only have a reason to exist if their "parent" equipment is being packed.
- **Example:**
  - `נינג׳ה גריל` (Parent)
    - ↳ `מלקחיים` (Child)
    - ↳ `נייר אפייה מותאם לנינג'ה` (Child)
    - ↳ `תרסיס שמן` (Child)
- **Behavior:** If the parent item is unchecked or omitted, the dependent items are automatically hidden or dimmed. (Can also be combined with Modular Add-on Packs below).
- **Status:** Backlog / High UX Value.

---

## 2. 🧩 Modular "Add-on Packs" / Mini-Templates (Mix & Match)
- **Concept:** Instead of maintaining many monolithic templates for every permutation of trip, allow injecting small modular "equipment packs" (5–10 items) into any active trip with a single click.
- **Examples:**
  - `+ הוסף ערכת חורף / גשם 🌧️`
  - `+ הוסף ערכת בריכה ומעיינות 🏊‍♂️`
  - `+ הוסף ערכת נינג'ה גריל / מנגל 🥩`
- **Behavior:** Appends the mini-template's items into the matching categories of the active trip without overwriting existing items.
- **Status:** Backlog / High UX Value.

---

## 3. ⚡ "Last-Minute / Morning-Of" Flag (דקה 90 / בוקר היציאה)
- **Concept:** Distinguish between items packed the night before and items that can only be packed right before walking out the door on departure morning.
- **Examples:** Toothbrushes, bedside phone chargers, chilled food/pancakes from the fridge, laptop, daily medications.
- **Behavior:**
  - Lightweight toggle (`⚡ דקה 90`) on an item.
  - Quick filter chip at the top of the trip view so on departure morning the family sees *only* the final sweep items.
- **Status:** Backlog.

---

## 4. 🛒 "Need to Buy" Pre-Trip Status / Shopping Filter (להשלים בקניות)
- **Concept:** Reviewing the packing list a few days before the trip often reveals missing or depleted items (e.g., sunscreen, mosquito spray, wine, road snacks).
- **Behavior:**
  - Ability to mark an item as `🛒 לקנות` (Need to Buy).
  - Filter by `🛒 לקנות` while at the supermarket, or share just the shopping list to WhatsApp. Once bought, transitioning it back to normal unpacked state ready for packing.
- **Status:** Backlog.

---

## 5. 🔄 "Return-Trip / Repacking Check" Mode (אריזה לחזרה הביתה)
- **Concept:** Prevent leaving chargers in wall sockets or favorite towels at the cabin when packing to return home, without cluttering the list with consumables that were already eaten or used.
- **Behavior:**
  - Mark food/disposable items as *Consumable* (`מתכלה`).
  - At the end of the vacation, trigger **"🔄 התארגנות לחזרה הביתה"**: unchecks all permanent gear so the family can verify everything goes back into the car, while hiding or ignoring consumables.
- **Status:** Backlog.

---

## 6. 🧮 Duration / Nights Auto-Scaler (מחשבון כמויות לפי מספר לילות)
- **Concept:** Templates are typically calibrated for a baseline duration (e.g., 2 nights = 15 sets of daily clothes & underwear for 5 people). Longer trips require scaling per-day items while keeping fixed gear at `1`.
- **Behavior:**
  - Optional item scaling rule (`fixed` vs. `per_night`).
  - When cloning a template into a new trip, prompt for the number of nights and automatically calculate the quantities for `per_night` items.
- **Status:** Backlog.

---

## 7. 🔑 "Pre-Departure House Checklist" Section (סגירת הבית לפני יציאה)
- **Concept:** Final peace-of-mind verification right before locking the front door.
- **Examples:** Take out trash, turn off ACs & water heater, close shutters/windows, pause/run robot vacuum, lock back doors.
- **Behavior:** A dedicated collapsible checklist block or special category at the bottom of the trip view so departure tasks live in the same place as the final packing sweep.
- **Status:** Backlog.

---

## 8. 📲 Installable PWA + Offline Asset Caching (אפליקציית מסך בית מלאה)
- **Concept:** True native-app feel on iOS and Android with zero-latency launch even with zero cellular reception (e.g., underground parking or remote nature spots).
- **Behavior:**
  - Add Web App Manifest (`manifest.json`) with RTL metadata, app icons, and standalone display mode ("Add to Home Screen").
  - Add a Service Worker to cache static shell assets (`index.html`, CSS, JS, fonts) alongside the existing `localStorage` data cache and offline mutation queue.
- **Status:** Backlog.

---

## 9. 👥 Individual Family Member Packing Views
- **Concept:** "My Packing Mode" — a focused view where a kid or parent sees *only* the items assigned to their name with extra-large touch targets.
- **Status:** Backlog.

---

## 10. 🎒 Bag / Container Organization (חלוקה לתיקים / מיקום ברכב)
- **Concept:** Know which bag holds which item (e.g., `🚗 תיק לאוטו`, `🏖️ תיק בריכה נגיש`, `🧊 צידנית`, `🧳 מזוודה`) so you don't unpack the entire trunk on the way north just to find swimsuits or snacks.
- **⚠️ Design Constraint (Requires Further UX Design):**
  - Adding a second set of colored tag pills next to family member assignees on every item row risks making the mobile UI visually cluttered and overwhelming.
  - **Directions to explore before implementation:**
    1. *View-Mode Switching:* Keep bags hidden during normal category view, and only show/assign them in a dedicated "Packing into Bags" view.
    2. *Sub-headers or subtle icons:* Use a single subtle icon or group-by-bag toggle rather than additional text badges on each row.
- **Status:** Needs UX/UI Design Simplification.

---

## ✅ Completed Features

### 📴 Offline Mutations Queue & Reconciliation
- **Concept:** Full offline usage (e.g., in airplane mode or spotty mobile reception).
- **Implementation:**
  - Mutations (`packed`, note edits, quantity changes) are buffered and coalesced in `localStorage` (`frontend/js/offline-queue.js`).
  - Local trip & member snapshots cached in `localStorage` for offline page reloads.
  - Sequential replay upon WebSocket reconnection with automatic state reconciliation.
- **Status:** ✅ Completed.
