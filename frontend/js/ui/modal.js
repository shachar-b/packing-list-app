/**
 * Accessible Modal & Drawer Manager.
 * Handles stacking order, backdrop clicks, and Escape key dismissal.
 */

class ModalManager {
  constructor() {
    this.stack = [];

    // Global keyboard listener for Escape key (top-most modal first)
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.stack.length > 0) {
        e.preventDefault();
        const top = this.stack[this.stack.length - 1];
        this.close(top.id);
      }
    });
  }

  open({ id, contentHtml, isDrawer = false, onClose = null, onOpen = null }) {
    // If modal already open, close it first
    if (this.stack.some((m) => m.id === id)) {
      this.close(id);
    }

    const previousActiveElement = document.activeElement;

    // Create backdrop container
    const backdrop = document.createElement('div');
    backdrop.id = `modal-backdrop-${id}`;
    backdrop.className = `modal-backdrop ${isDrawer ? 'drawer-backdrop' : ''}`;
    backdrop.setAttribute('role', 'dialog');
    backdrop.setAttribute('aria-modal', 'true');

    // Dialog wrapper
    const dialog = document.createElement('div');
    dialog.className = isDrawer ? 'modal-dialog modal-drawer' : 'modal-dialog';
    dialog.innerHTML = contentHtml;

    backdrop.appendChild(dialog);

    // Backdrop click dismissal (only when clicking the backdrop itself, not dialog content)
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        this.close(id);
      }
    });

    // Close buttons inside dialog with data-dismiss="modal"
    const closeButtons = dialog.querySelectorAll('[data-dismiss="modal"]');
    closeButtons.forEach((btn) => {
      btn.addEventListener('click', () => this.close(id));
    });

    document.body.appendChild(backdrop);

    // Trigger CSS animation
    requestAnimationFrame(() => {
      backdrop.classList.add('is-active');
      // Autofocus first input or primary button if present
      const focusable = dialog.querySelector('input:not([type="hidden"]), select, textarea, button.btn-primary, [autofocus]');
      if (focusable) {
        focusable.focus();
      }
    });

    const modalObj = {
      id,
      backdrop,
      dialog,
      previousActiveElement,
      onClose,
    };

    this.stack.push(modalObj);

    if (onOpen) {
      onOpen(dialog);
    }

    return dialog;
  }

  close(id) {
    const idx = this.stack.findIndex((m) => m.id === id);
    if (idx === -1) return;

    const modalObj = this.stack[idx];
    this.stack.splice(idx, 1);

    modalObj.backdrop.classList.remove('is-active');

    setTimeout(() => {
      if (modalObj.backdrop.parentNode) {
        modalObj.backdrop.parentNode.removeChild(modalObj.backdrop);
      }
      if (modalObj.onClose) {
        modalObj.onClose();
      }
      if (modalObj.previousActiveElement && document.contains(modalObj.previousActiveElement)) {
        try { modalObj.previousActiveElement.focus(); } catch (e) {}
      }
    }, 200);
  }

  closeTop() {
    if (this.stack.length > 0) {
      this.close(this.stack[this.stack.length - 1].id);
    }
  }

  closeAll() {
    while (this.stack.length > 0) {
      this.close(this.stack[this.stack.length - 1].id);
    }
  }
}

export const modal = new ModalManager();
