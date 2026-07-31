/* cru.js — AJAX CRUD helpers + Toast feedback */
const $cru = e => document.querySelector(e);
const $crus = e => document.querySelectorAll(e);

function cruCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

let $cruConfig = {
  prefix_url: '',
  headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': cruCsrfToken() },
  callbacks: {}
};

function $C(opts) {
  if (opts) for (let k of Object.keys(opts)) $cruConfig[k] = opts[k];
  $cruLoadEvents();
}

/* ── Toast system ── */
function cruToast(msg, type) {
  type = type || 'success';
  let container = document.getElementById('cru-toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'cru-toast-container';
    container.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:8px';
    document.body.appendChild(container);
  }
  const colors = { success: '#059669', danger: '#dc2626', warning: '#d97706', info: '#3b82f6' };
  const bg = colors[type] || colors.info;
  const el = document.createElement('div');
  el.style.cssText = `background:${bg};color:#fff;padding:12px 20px;border-radius:8px;font-size:0.9rem;font-weight:500;box-shadow:0 4px 12px rgba(0,0,0,0.15);transition:opacity 0.3s;display:flex;align-items:center;gap:8px;max-width:360px`;
  el.innerHTML = msg;
  container.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 300); }, 3000);
}

/* ── Load events ── */
function $cruLoadEvents() {
  $cruLoadRequests();
  $cruLoadFormIntercept();
  $cruLoadAllContainers();
}

/* ── Container loading ── */
async function $cruLoadContainer(el) {
  el.classList.add('loaded');
  const parent = el.closest('[c-container]') || el;
  const url = parent.getAttribute('c-container');
  const targetSel = parent.getAttribute('c-target') || false;
  const type = parent.getAttribute('c-type') || 'html';
  const cb = parent.getAttribute('c-callback') || false;
  const resp = await fetch($cruConfig.prefix_url + url, { method: 'GET', headers: $cruConfig.headers });
  const html = await $cruTypeResponse(type, resp);
  const target = targetSel ? $cru(targetSel) : parent;
  if (targetSel || type !== 'off') {
    if (targetSel) target.innerHTML = html;
    else if (type === 'html') target.innerHTML = html;
  }
  if (cb) $cruConfig.callbacks[cb](html, target);
  $cruLoadEvents();
}

function $cruLoadAllContainers() {
  $crus('[c-container]:not(.loaded)').forEach(async el => { el.classList.add('loaded'); $cruLoadContainer(el); });
  $crus('[c-reload]:not(.loaded)').forEach(async el => {
    el.classList.add('loaded');
    el.addEventListener('click', () => $cruLoadContainer(el));
  });
}

/* ── Request handler ── */
async function cruRequest(el, method) {
  const url = el.getAttribute(`c-${method}`);
  const type = el.getAttribute('c-type') || 'html';
  const reloadContainer = el.getAttribute('c-reload-container') || false;
  const removeClosest = el.getAttribute('c-remove-closest') || false;
  const selfRemove = el.getAttribute('c-self-remove') || false;
  const redirect = el.getAttribute('c-redirect') || false;
  const swap = el.getAttribute('c-swap') || false;
  const append = el.getAttribute('c-append') || false;
  const prepend = el.getAttribute('c-prepend') || false;
  const cb = el.getAttribute('c-callback') || false;
  const targetSel = el.getAttribute('c-target') || false;

  const resp = await fetch($cruConfig.prefix_url + url, { method, headers: { ...$cruConfig.headers, 'X-CSRFToken': cruCsrfToken() } });
  const html = await $cruTypeResponse(type, resp);
  const target = targetSel && $cru(targetSel);

  if (resp.ok && method === 'DELETE') cruToast('Excluído com sucesso!', 'success');

  if (removeClosest) el.closest(removeClosest).remove();
  if (selfRemove) el.remove();
  if (swap) { $cru(swap).outerHTML = html; }
  if (append) { $cru(append).insertAdjacentHTML('beforeend', html); }
  if (prepend) { $cru(prepend).insertAdjacentHTML('afterbegin', html); }
  if (reloadContainer) $cruLoadContainer(el);
  if (target) {
    if (targetSel) target.innerHTML = html;
    else if (type === 'html') el.innerHTML = html;
  }
  if (cb) $cruConfig.callbacks[cb](html, target);
  $cruLoadEvents();
  if (redirect) window.location.href = redirect;
}

/* ── Bind c-delete / c-get buttons ── */
function $cruLoadRequests() {
  ['delete', 'get', 'post', 'put'].forEach(method => {
    const attr = `c-${method}`;
    $crus(`[${attr}]:not(.loaded)`).forEach(el => {
      el.classList.add('loaded');
      if (method === 'delete' && !el.hasAttribute('c-no-confirm')) {
        el.addEventListener('click', e => {
          if (!confirm('Tem certeza?')) { e.preventDefault(); return false; }
          cruRequest(el, method.toUpperCase());
        });
      } else {
        el.addEventListener('click', () => cruRequest(el, method.toUpperCase()));
      }
    });
  });
}

/* ── Form interception ── */
function $cruLoadFormIntercept() {
  $crus('form.c-form:not(.loaded)').forEach(form => {
    form.classList.add('loaded');
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const target = form.getAttribute('c-target') || false;
      const type = form.getAttribute('c-type') || 'html';
      const cb = form.getAttribute('c-callback') || false;
      const data = new FormData(form);
      if (!data.has('csrf_token')) data.append('csrf_token', cruCsrfToken());
      const url = form.getAttribute('action') || form.getAttribute('c-action') || form.action;
      const method = form.getAttribute('method') || 'GET';
      const resp = await fetch(url, { method, body: method === 'GET' ? undefined : data, headers: method === 'GET' ? $cruConfig.headers : {} });
      const result = await $cruTypeResponse(type, resp);
      if (target && type !== 'json') $cru(target).innerHTML = result;
      if (target && type === 'json') $cru(target).textContent = JSON.stringify(result, null, 2);
      if (cb) $cruConfig.callbacks[cb](result);
      $cruLoadEvents();
    });
  });
}

/* ── Response parser ── */
async function $cruTypeResponse(type, resp) {
  if (type === 'json') return resp.json();
  return resp.text();
}

/* ── Session timer ── */
function cruInitSessionTimer() {
  const meta = document.querySelector('meta[name="session-time"]');
  if (!meta) return;
  const loginTime = meta.getAttribute('content');
  if (!loginTime) return;
  const inicio = new Date(loginTime);
  function tick() {
    const diff = Math.floor((Date.now() - inicio.getTime()) / 1000);
    const el = document.getElementById('session-time');
    if (el) {
      const h = Math.floor(diff / 3600);
      const m = Math.floor((diff % 3600) / 60);
      const s = diff % 60;
      el.textContent =
        String(h).padStart(2, '0') + ':' +
        String(m).padStart(2, '0') + ':' +
        String(s).padStart(2, '0');
    }
  }
  tick();
  setInterval(tick, 1000);
}

/* ── Filtro responsavel por setor ── */
document.addEventListener('change', e => {
  if (!e.target.matches('select[name="setor_id"]')) return;
  const form = e.target.closest('form');
  const respSelect = form && form.querySelector('select[name="responsavel_id"]');
  if (!respSelect) return;
  const setorId = e.target.value;
  const val = respSelect.value;
  Array.from(respSelect.options).forEach(opt => {
    if (!opt.value) return;
    opt.hidden = setorId && opt.dataset.setor !== setorId;
  });
  if (val && respSelect.querySelector(`option[value="${val}"]`)?.hidden) {
    respSelect.value = '';
  }
});

/* ── Lightbox ── */
function abrirLightbox(src, nome) {
  const overlay = document.createElement('div');
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;cursor:pointer;padding:20px';
  overlay.onclick = () => overlay.remove();
  const img = document.createElement('img');
  img.src = src;
  img.alt = nome || '';
  img.style.cssText = 'max-width:90vw;max-height:90vh;border-radius:8px;box-shadow:0 8px 32px rgba(0,0,0,0.5);object-fit:contain';
  overlay.appendChild(img);
  document.body.appendChild(overlay);
}

/* ── Init ── */
document.addEventListener('DOMContentLoaded', () => {
  $cruLoadEvents();
  cruInitSessionTimer();
});
