// Sidebar
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('sidebarOverlay');
function openSidebar() { sidebar?.classList.add('open'); overlay?.classList.add('open'); }
function closeSidebar() { sidebar?.classList.remove('open'); overlay?.classList.remove('open'); }
document.getElementById('menuBtn')?.addEventListener('click', openSidebar);
document.getElementById('sidebarClose')?.addEventListener('click', closeSidebar);
overlay?.addEventListener('click', closeSidebar);
document.addEventListener('keydown', e => { if (e.key === 'Escape') { closeSidebar(); closeAllDropdowns(); closeAllModals(); } });

// Dropdowns
function closeAllDropdowns() {
  document.querySelectorAll('.dropdown-panel').forEach(p => p.classList.remove('open'));
}
document.querySelectorAll('[data-dropdown]').forEach(btn => {
  btn.addEventListener('click', e => {
    e.stopPropagation();
    const target = document.getElementById(btn.dataset.dropdown);
    const isOpen = target?.classList.contains('open');
    closeAllDropdowns();
    if (!isOpen) target?.classList.add('open');
  });
});
document.addEventListener('click', closeAllDropdowns);

// Modals
function openModal(id) { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }
function closeAllModals() { document.querySelectorAll('.modal-backdrop').forEach(m => m.classList.remove('open')); }
document.querySelectorAll('[data-modal-open]').forEach(btn => {
  btn.addEventListener('click', () => openModal(btn.dataset.modalOpen));
});
document.querySelectorAll('[data-modal-close]').forEach(btn => {
  btn.addEventListener('click', () => closeModal(btn.dataset.modalClose));
});
document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
  backdrop.addEventListener('click', e => { if (e.target === backdrop) backdrop.classList.remove('open'); });
});

// Edit buttons — fill form fields from data attributes
document.querySelectorAll('[data-edit-modal]').forEach(btn => {
  btn.addEventListener('click', () => {
    const modalId = btn.dataset.editModal;
    const modal = document.getElementById(modalId);
    if (!modal) return;
    Object.entries(btn.dataset).forEach(([key, val]) => {
      if (key === 'editModal') return;
      const field = modal.querySelector(`[name="${key}"]`) || modal.querySelector(`#${key}`);
      if (field) field.value = val;
    });
    // Update form action URL
    const form = modal.querySelector('form');
    if (form && btn.dataset.actionUrl) form.action = btn.dataset.actionUrl;
    openModal(modalId);
  });
});

// Delete confirmation
document.querySelectorAll('[data-delete-form]').forEach(btn => {
  btn.addEventListener('click', () => {
    if (confirm('Tem certeza que deseja excluir? Esta ação não pode ser desfeita.')) {
      const form = document.getElementById(btn.dataset.deleteForm);
      form?.submit();
    }
  });
});

// Config tabs
document.querySelectorAll('.config-menu-item[data-section]').forEach(item => {
  item.addEventListener('click', () => {
    document.querySelectorAll('.config-menu-item').forEach(i => i.classList.remove('active'));
    document.querySelectorAll('.config-section').forEach(s => s.classList.remove('active'));
    item.classList.add('active');
    document.getElementById(item.dataset.section)?.classList.add('active');
  });
});

// Auto-dismiss flash messages
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(f => f.style.opacity = '0');
  setTimeout(() => document.querySelectorAll('.flash').forEach(f => f.remove()), 400);
}, 4000);
