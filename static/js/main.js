/**
 * main.js — SmartPOS Cafe & Retail Management
 * Global JavaScript utilities
 */

// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });

  // Confirm delete links
  document.querySelectorAll('[id^="del_"]').forEach(btn => {
    btn.addEventListener('click', function (e) {
      if (!confirm('Yakin ingin menghapus data ini?')) {
        e.preventDefault();
      }
    });
  });

  // Number input formatting hint
  document.querySelectorAll('input[type="number"]').forEach(input => {
    input.addEventListener('wheel', e => e.preventDefault());
  });
});

// Format number as Rupiah
function formatRupiah(num) {
  return 'Rp ' + parseInt(num).toLocaleString('id-ID');
}
