/* ═══════════════════════════════════════════════════════════
   dashboard.js  —  DataVision AI
   Handles: sidebar, section nav, quality, stats,
            chart builder, clustering, AI insights
   ═══════════════════════════════════════════════════════════ */

/* ── Sidebar toggle ────────────────────────────────────────── */
const sidebar       = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
sidebarToggle?.addEventListener('click', () => sidebar.classList.toggle('open'));

/* ── Active sidebar link ───────────────────────────────────── */
document.querySelectorAll('.sb-link').forEach(link => {
  link.addEventListener('click', () => {
    document.querySelectorAll('.sb-link').forEach(l => l.classList.remove('active'));
    link.classList.add('active');
    if (window.innerWidth <= 900) sidebar.classList.remove('open');
  });
});

/* ── Intersection observer: auto-highlight sidebar ─────────── */
const sections = document.querySelectorAll('.dash-section');
const observer = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      const id = e.target.id.replace('sec-', '');
      document.querySelectorAll('.sb-link').forEach(l => {
        l.classList.toggle('active', l.dataset.section === id);
      });
    }
  });
}, { threshold: 0.3 });
sections.forEach(s => observer.observe(s));


/* ══════════════════════════════════════════════════════════════
   DATA QUALITY
   ══════════════════════════════════════════════════════════════ */
async function loadQuality() {
  try {
    const res  = await fetch('/api/quality');
    const data = await res.json();
    if (data.error) { showError('qualityTable', data.error); return; }

    document.getElementById('qualityTable').innerHTML = `<div class="table-scroll">${data.table}</div>`;

    const dupEl = document.getElementById('qualityDupes');
    if (data.duplicates > 0) {
      dupEl.style.display = 'block';
      dupEl.innerHTML = `<i class="fa-solid fa-copy"></i>
        <strong>${data.duplicates.toLocaleString()} duplicate rows</strong> detected.
        Consider removing them before analysis.`;
    }
  } catch (err) {
    showError('qualityTable', 'Failed to load quality report.');
  }
}


/* ══════════════════════════════════════════════════════════════
   DESCRIPTIVE STATISTICS
   ══════════════════════════════════════════════════════════════ */
async function loadStats() {
  try {
    const res  = await fetch('/api/stats');
    const data = await res.json();
    if (data.error) { showError('statsTable', data.error); return; }
    document.getElementById('statsTable').innerHTML = `<div class="table-scroll">${data.table}</div>`;
  } catch (err) {
    showError('statsTable', 'Failed to load statistics.');
  }
}


/* ══════════════════════════════════════════════════════════════
   CHART BUILDER
   ══════════════════════════════════════════════════════════════ */
const chartType  = document.getElementById('chartType');
const genBtn     = document.getElementById('genChartBtn');
const chartCard  = document.getElementById('chartCard');
const chartError = document.getElementById('chartError');

/* Show / hide fields based on chart type */
function updateFormFields() {
  const t = chartType.value;
  const show = (id, visible) => {
    const el = document.getElementById(id);
    if (el) el.style.display = visible ? '' : 'none';
  };
  show('fgX',    t !== 'heatmap');
  show('fgY',    !['histogram','pie','heatmap'].includes(t));
  show('fgColor',!['histogram','pie','heatmap'].includes(t));
  show('fgAgg',  t === 'bar');
  show('fgSize', t === 'bubble');
}
chartType.addEventListener('change', updateFormFields);
updateFormFields();

genBtn.addEventListener('click', async () => {
  const t    = chartType.value;
  const xSel = document.getElementById('chartX')?.value;
  const ySel = document.getElementById('chartY')?.value;
  const col  = document.getElementById('chartColor')?.value;
  const agg  = document.getElementById('chartAgg')?.value;
  const sz   = document.getElementById('chartSize')?.value;

  genBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating…';
  genBtn.disabled  = true;
  chartCard.style.display  = 'none';
  chartError.style.display = 'none';

  try {
    const res  = await fetch('/api/chart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: t, x: xSel, y: ySel, color: col, agg, size: sz }),
    });
    const data = await res.json();

    if (data.error) {
      chartError.style.display = 'block';
      chartError.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> ${data.error}`;
    } else {
      chartCard.style.display = 'block';
      const fig = JSON.parse(data.chart);
      Plotly.newPlot('chartPlot', fig.data, {
        ...fig.layout,
        paper_bgcolor: 'transparent',
        plot_bgcolor:  'transparent',
        font: { color: '#e2e8f0', family: 'Segoe UI, system-ui, sans-serif' },
      }, { responsive: true, displayModeBar: true });
    }
  } catch (err) {
    chartError.style.display = 'block';
    chartError.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> Network error: ${err.message}`;
  } finally {
    genBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Generate Chart';
    genBtn.disabled  = false;
  }
});


/* ══════════════════════════════════════════════════════════════
   K-MEANS CLUSTERING
   ══════════════════════════════════════════════════════════════ */
const kSlider      = document.getElementById('kSlider');
const kVal         = document.getElementById('kVal');
const runClusterBtn= document.getElementById('runClusterBtn');

kSlider.addEventListener('input', () => { kVal.textContent = `k = ${kSlider.value}`; });

runClusterBtn.addEventListener('click', async () => {
  const k = parseInt(kSlider.value);
  const checked = [...document.querySelectorAll('#clusterCols input:checked')].map(c => c.value);

  if (checked.length < 2) {
    showError('clusterError', 'Please select at least 2 numeric features.');
    return;
  }

  document.getElementById('clusterResults').style.display = 'none';
  document.getElementById('clusterError').style.display   = 'none';
  document.getElementById('clusterLoader').style.display  = 'flex';
  runClusterBtn.disabled = true;
  runClusterBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running…';

  try {
    const res  = await fetch('/api/cluster', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ k, columns: checked }),
    });
    const data = await res.json();

    if (data.error) {
      document.getElementById('clusterError').style.display = 'block';
      document.getElementById('clusterError').innerHTML =
        `<i class="fa-solid fa-circle-xmark"></i> ${data.error}`;
    } else {
      document.getElementById('clusterResults').style.display = 'block';

      /* Metrics */
      document.getElementById('silScore').textContent    = data.silhouette;
      document.getElementById('varExplained').textContent=
        `${data.variance_explained[0]}% + ${data.variance_explained[1]}%`;
      document.getElementById('kUsed').textContent = data.k;

      /* Scatter */
      const figS = JSON.parse(data.scatter);
      Plotly.newPlot('clusterScatter', figS.data, {
        ...figS.layout,
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        font: { color: '#e2e8f0', family: 'Segoe UI, system-ui, sans-serif' },
      }, { responsive: true });

      /* Elbow */
      const figE = JSON.parse(data.elbow);
      Plotly.newPlot('clusterElbow', figE.data, {
        ...figE.layout,
        paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
        font: { color: '#e2e8f0', family: 'Segoe UI, system-ui, sans-serif' },
      }, { responsive: true });

      /* Summary table */
      document.getElementById('clusterSummary').innerHTML = data.cluster_summary;
    }
  } catch (err) {
    document.getElementById('clusterError').style.display = 'block';
    document.getElementById('clusterError').innerHTML =
      `<i class="fa-solid fa-circle-xmark"></i> Network error: ${err.message}`;
  } finally {
    document.getElementById('clusterLoader').style.display = 'none';
    runClusterBtn.disabled = false;
    runClusterBtn.innerHTML = '<i class="fa-solid fa-play"></i> Run Clustering';
  }
});


/* ══════════════════════════════════════════════════════════════
   AI INSIGHTS
   ══════════════════════════════════════════════════════════════ */
async function loadInsights() {
  const grid   = document.getElementById('insightsGrid');
  const loader = document.getElementById('insightsLoader');
  const errEl  = document.getElementById('insightsError');

  try {
    const res  = await fetch('/api/insights');
    const data = await res.json();

    loader.style.display = 'none';

    if (data.error) {
      errEl.style.display = 'block';
      errEl.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> ${data.error}`;
      return;
    }

    grid.style.display = 'grid';
    grid.innerHTML = data.insights.map(ins => `
      <div class="insight-card">
        <div class="insight-top">
          <span class="insight-icon">${ins.icon}</span>
          <div class="insight-meta">
            <span class="insight-cat">${ins.cat}</span>
            <span class="insight-title">${ins.title}</span>
          </div>
        </div>
        <p class="insight-text">${ins.text}</p>
      </div>
    `).join('');
  } catch (err) {
    loader.style.display = 'none';
    errEl.style.display  = 'block';
    errEl.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> Failed to load insights.`;
  }
}


/* ══════════════════════════════════════════════════════════════
   UTILITY
   ══════════════════════════════════════════════════════════════ */
function showError(containerId, msg) {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = `<div class="error-box"><i class="fa-solid fa-circle-xmark"></i> ${msg}</div>`;
}


/* ══════════════════════════════════════════════════════════════
   INIT — load everything on page ready
   ══════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  loadQuality();
  loadStats();
  loadInsights();
});
