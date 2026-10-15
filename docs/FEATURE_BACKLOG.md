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
- **Behavior:** If the parent item is unchecked or omitted, the dependent items are automatically hidden or dimmed.
- **Status:** Backlog / High UX Value.

---

## 2. 📴 Offline Mutations Queue & Reconciliation
- **Concept:** Allow full offline usage (e.g., in airplane mode or spotty mobile reception).
- **Behavior:**
  - Mutations (`packed`, note edits, quantity changes) are buffered in `localStorage` or `IndexedDB`.
  - When reconnected, changes are played back sequentially.
  - Conflict resolution using granular field-level updates and timestamps.
- **Status:** In Progress.

---

## 3. 👥 Individual Family Member Packing Views
- **Concept:** "My Packing Mode" — a quick toggle where a kid or parent sees *only* the items assigned to their name with extra-large checkboxes.
- **Status:** Backlog.
