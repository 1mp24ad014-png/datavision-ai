/* landing.js — drag & drop + file picker */

const dropZone  = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileInfo  = document.getElementById('fileInfo');
const submitBtn = document.getElementById('submitBtn');
const uploadForm= document.getElementById('uploadForm');

function setFile(file) {
  if (!file) return;
  const allowed = ['csv','xlsx','xls'];
  const ext = file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) {
    fileInfo.textContent = '❌ Unsupported file type. Use CSV or Excel.';
    fileInfo.style.color = '#ef4444';
    submitBtn.disabled = true;
    return;
  }
  const size = (file.size / 1024 / 1024).toFixed(2);
  fileInfo.textContent = `✅ ${file.name}  (${size} MB)`;
  fileInfo.style.color = '#10b981';
  submitBtn.disabled = false;
}

fileInput.addEventListener('change', () => setFile(fileInput.files[0]));

dropZone.addEventListener('dragover', e => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) {
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;
    setFile(file);
  }
});

uploadForm.addEventListener('submit', () => {
  submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Uploading…';
  submitBtn.disabled = true;
});

/* Auto-dismiss flash messages */
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(el => {
    el.style.transition = 'opacity 0.5s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 500);
  });
}, 4000);
