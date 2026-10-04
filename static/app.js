let applications = [];

function statusLabel(s) {
  const map = { applied: 'Applied', screening: 'Screening', interview: 'Interview', offer: 'Offer', rejected: 'Rejected', withdrawn: 'Withdrawn' };
  return map[s] || s;
}

function matchLabel(m) {
  const map = { low: 'Low match', medium: 'Medium match', strong: 'Strong match' };
  return map[m] || '';
}

function showError(msg) {
  const wrap = document.querySelector('.wrap');
  let banner = document.getElementById('error-banner');
  if (!banner) {
    banner = document.createElement('div');
    banner.id = 'error-banner';
    banner.className = 'error-banner';
    wrap.insertBefore(banner, wrap.children[2]);
  }
  banner.textContent = msg;
  banner.style.display = 'block';
}

function clearError() {
  const banner = document.getElementById('error-banner');
  if (banner) banner.style.display = 'none';
}

async function loadAll() {
  try {
    const res = await fetch('/api/applications');
    if (!res.ok) throw new Error('Failed to load applications');
    applications = await res.json();
    clearError();
  } catch (e) {
    applications = [];
    showError('Could not load applications.csv. Is the Flask server running?');
  }
  render();
}

async function createApplication(payload) {
  const res = await fetch('/api/applications', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || 'Failed to save application.');
  }
  return res.json();
}

async function updateApplication(id, payload) {
  const res = await fetch('/api/applications/' + id, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || 'Failed to update application.');
  }
}

async function deleteApplication(id) {
  try {
    const res = await fetch('/api/applications/' + id, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete application.');
    applications = applications.filter(a => a.id !== id);
    render();
  } catch (e) {
    showError(e.message);
  }
}

function renderStats() {
  const counts = { applied: 0, screening: 0, interview: 0, offer: 0, rejected: 0 };
  applications.forEach(a => { if (counts[a.status] !== undefined) counts[a.status]++; });
  const statsEl = document.getElementById('stats');
  statsEl.innerHTML = ['applied', 'screening', 'interview', 'offer', 'rejected'].map(s =>
    '<div class="stat"><div class="num">' + counts[s] + '</div><div class="label">' + statusLabel(s) + '</div></div>'
  ).join('');
}

function render() {
  renderStats();
  const filterStatus = document.getElementById('filter-status').value;
  const search = document.getElementById('search').value.toLowerCase();
  const listEl = document.getElementById('list');

  let filtered = applications.filter(a => {
    if (filterStatus !== 'all' && a.status !== filterStatus) return false;
    if (search && !((a.company || '') + ' ' + (a.role || '')).toLowerCase().includes(search)) return false;
    return true;
  });

  if (filtered.length === 0) {
    listEl.innerHTML = '<div class="empty">No applications yet. Add your first one above.</div>';
    return;
  }

  const statusTier = s => {
    if (s === 'rejected') return 3;
    if (s === 'withdrawn') return 2;
    if (s === 'applied') return 1;
    return 0; // screening, interview, offer
  };
  filtered.sort((a, b) => {
    const tierDiff = statusTier(a.status) - statusTier(b.status);
    if (tierDiff !== 0) return tierDiff;
    return (b.dateApplied || '').localeCompare(a.dateApplied || '');
  });

  listEl.innerHTML = filtered.map((a, i) => {
    const sepHtml = (i > 0 && statusTier(a.status) !== statusTier(filtered[i - 1].status))
      ? '<hr class="tier-sep tier-sep-' + a.status + '">'
      : '';
    const linkHtml = a.link ? '<a href="' + a.link + '" target="_blank" rel="noopener">Job link</a>' : '';
    const matchHtml = matchLabel(a.matchQuality) ? '<span class="badge match-' + a.matchQuality + '">' + matchLabel(a.matchQuality) + '</span>' : '';
    const agoHtml = (a.status !== 'rejected' && a.status !== 'withdrawn' && a.dateApplied) ? applicationAgeHtml(a.dateApplied) : '';
    return sepHtml + '<div class="card status-' + a.status + '">' +
      '<div class="card-top">' +
        '<div><div class="card-title">' + escapeHtml(a.company) + agoHtml + '</div><div class="card-role">' + escapeHtml(a.role) + '</div></div>' +
        '<div class="badges">' + matchHtml + '<span class="badge status-' + a.status + '">' + statusLabel(a.status) + '</span></div>' +
      '</div>' +
      '<div class="meta-row">' +
        (a.dateApplied ? '<span>Applied ' + formatDate(a.dateApplied) + '</span>' : '') +
        (a.salary ? '<span>' + escapeHtml(a.salary) + '</span>' : '') +
        (linkHtml ? '<span>' + linkHtml + '</span>' : '') +
      '</div>' +
      (a.matchReason ? '<div class="notes match-reason"><strong>Match:</strong> ' + escapeHtml(a.matchReason) + '</div>' : '') +
      (a.notes ? '<div class="notes">' + escapeHtml(a.notes) + '</div>' : '') +
      '<div class="card-actions">' +
        '<button onclick="editApplication(\'' + a.id + '\')">Edit</button>' +
        '<button onclick="deleteApplication(\'' + a.id + '\')">Delete</button>' +
      '</div>' +
    '</div>';
  }).join('');
}

function applicationAgeHtml(dateStr) {
  const applied = new Date(dateStr + 'T00:00:00');
  if (isNaN(applied)) return '';
  const days = Math.floor((Date.now() - applied.getTime()) / 86400000);
  if (days < 0) return '';
  const ageClass = days > 30 ? 'age-red' : days > 14 ? 'age-orange' : '';
  return ' - <span class="applied-ago ' + ageClass + '">applied ' + timeAgoText(days) + '</span>';
}

function timeAgoText(days) {
  if (days < 1) return 'today';
  if (days === 1) return '1 day ago';
  if (days < 14) return days + ' days ago';
  if (days < 60) {
    const weeks = Math.floor(days / 7);
    return weeks + (weeks === 1 ? ' week ago' : ' weeks ago');
  }
  const months = Math.floor(days / 30);
  return months + (months === 1 ? ' month ago' : ' months ago');
}

function formatDate(dateStr) {
  const [year, month, day] = dateStr.split('-');
  if (!year || !month || !day) return dateStr;
  return day + '/' + month + '/' + year;
}

function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s || '';
  return div.innerHTML;
}

function clearForm() {
  document.getElementById('edit-id').value = '';
  document.getElementById('f-company').value = '';
  document.getElementById('f-role').value = '';
  document.getElementById('f-date').value = '';
  document.getElementById('f-status').value = 'applied';
  document.getElementById('f-match').value = '';
  document.getElementById('f-match-reason').value = '';
  document.getElementById('f-salary').value = '';
  document.getElementById('f-link').value = '';
  document.getElementById('f-notes').value = '';
  document.getElementById('form-title').textContent = 'Add application';
  document.getElementById('save-btn').textContent = 'Add application';
  document.getElementById('cancel-btn').style.display = 'none';
}

function editApplication(id) {
  const app = applications.find(a => a.id === id);
  if (!app) return;
  document.getElementById('edit-id').value = app.id;
  document.getElementById('f-company').value = app.company || '';
  document.getElementById('f-role').value = app.role || '';
  document.getElementById('f-date').value = app.dateApplied || '';
  document.getElementById('f-status').value = app.status || 'applied';
  document.getElementById('f-match').value = app.matchQuality || '';
  document.getElementById('f-match-reason').value = app.matchReason || '';
  document.getElementById('f-salary').value = app.salary || '';
  document.getElementById('f-link').value = app.link || '';
  document.getElementById('f-notes').value = app.notes || '';
  document.getElementById('form-title').textContent = 'Edit application';
  document.getElementById('save-btn').textContent = 'Save changes';
  document.getElementById('cancel-btn').style.display = 'inline-block';
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

document.getElementById('save-btn').addEventListener('click', async () => {
  const company = document.getElementById('f-company').value.trim();
  const role = document.getElementById('f-role').value.trim();
  if (!company || !role) { alert('Company and role are required.'); return; }

  const editId = document.getElementById('edit-id').value;
  const payload = {
    company: company,
    role: role,
    dateApplied: document.getElementById('f-date').value,
    status: document.getElementById('f-status').value,
    matchQuality: document.getElementById('f-match').value,
    matchReason: document.getElementById('f-match-reason').value.trim(),
    salary: document.getElementById('f-salary').value.trim(),
    link: document.getElementById('f-link').value.trim(),
    notes: document.getElementById('f-notes').value.trim()
  };

  try {
    if (editId) {
      await updateApplication(editId, payload);
    } else {
      await createApplication(payload);
    }
    clearError();
    clearForm();
    await loadAll();
  } catch (e) {
    showError(e.message);
  }
});

document.getElementById('cancel-btn').addEventListener('click', clearForm);
document.getElementById('filter-status').addEventListener('change', render);
document.getElementById('search').addEventListener('input', render);

loadAll();
