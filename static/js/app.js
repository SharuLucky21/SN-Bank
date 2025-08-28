document.addEventListener('DOMContentLoaded', () => {
  // Tiny client-side helper for flash auto-hide
  const flashes = document.querySelectorAll('.flash');
  setTimeout(() => flashes.forEach(f => f.style.display = 'none'), 6500);
});
