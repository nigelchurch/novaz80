/* Full-screen pan-and-zoom viewer for schematics and diagrams, and the rotatable 3D boards. */
(() => {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const here = document.currentScript.src, base = here.slice(0, here.lastIndexOf('/js/') + 1);
  const el = (t, c, txt) => { const e = document.createElement(t); if (c) e.className = c; if (txt) e.textContent = txt; return e; };
  const btn = (label, txt, fn) => { const b = el('button', '', txt); b.type = 'button'; b.setAttribute('aria-label', label); b.addEventListener('click', fn); return b; };

  /* phone Back button closes whatever is open full screen */
  let closer = null;
  const pushBack = fn => { closer = fn; history.pushState({ viewer: 1 }, ''); };
  const popBack = () => { if (closer) { closer = null; if (history.state && history.state.viewer) history.back(); } };
  addEventListener('popstate', () => { if (closer) { const f = closer; closer = null; f(); } });

  /* ---------- pan and zoom ---------- */
  let dlg, stage, title, tabs, pdf, thing = null, W = 1, H = 1, k = 1, x = 0, y = 0, crisp = 1, timer = 0, fitK = 1;
  const pts = new Map();

  const build = () => {
    dlg = el('dialog', 'viewer');
    const bar = el('header');
    title = el('h2');
    tabs = el('div', 'vtabs');
    pdf = el('a', 'vpdf', 'PDF');
    pdf.target = '_blank';
    pdf.rel = 'noopener';
    const tools = el('div', 'vtools');
    tools.append(btn('Zoom out', '−', () => zoomMid(1 / 1.5)), btn('Fit to screen', 'Fit', fit), btn('Zoom in', '+', () => zoomMid(1.5)), pdf);
    bar.append(title, tabs, tools, btn('Close', '✕', () => dlg.close()));
    stage = el('div', 'vstage');
    stage.tabIndex = 0;
    stage.setAttribute('aria-label', 'Drag to move, pinch or scroll to zoom');
    dlg.append(bar, stage);
    document.body.append(dlg);
    dlg.addEventListener('close', () => { document.documentElement.classList.remove('locked'); stage.replaceChildren(); thing = null; pts.clear(); popBack(); });

    stage.addEventListener('pointerdown', e => { stage.setPointerCapture(e.pointerId); pts.set(e.pointerId, [e.clientX, e.clientY]); });
    stage.addEventListener('pointermove', e => {
      if (!pts.has(e.pointerId)) return;
      const before = [...pts.values()].map(p => [...p]);
      pts.set(e.pointerId, [e.clientX, e.clientY]);
      const now = [...pts.values()];
      if (now.length === 1) { x += now[0][0] - before[0][0]; y += now[0][1] - before[0][1]; }
      else {
        const mid = p => [(p[0][0] + p[1][0]) / 2, (p[0][1] + p[1][1]) / 2], gap = p => Math.hypot(p[0][0] - p[1][0], p[0][1] - p[1][1]) || 1;
        const a = mid(before), b = mid(now);
        x += b[0] - a[0]; y += b[1] - a[1];
        zoomAt(gap(now) / gap(before), b[0], b[1]);
      }
      draw();
    });
    const up = e => pts.delete(e.pointerId);
    stage.addEventListener('pointerup', up);
    stage.addEventListener('pointercancel', up);
    stage.addEventListener('wheel', e => { e.preventDefault(); zoomAt(Math.exp(-e.deltaY * (e.ctrlKey ? .01 : .0016)), e.clientX, e.clientY); draw(); }, { passive: false });
    let tap = 0;
    stage.addEventListener('click', e => {
      if (e.timeStamp - tap < 320) { if (k > fitK * 1.6) fit(); else { zoomAt(2.6, e.clientX, e.clientY); draw(); } tap = 0; } else tap = e.timeStamp;
    });
    stage.addEventListener('keydown', e => {
      const d = { ArrowLeft: [60, 0], ArrowRight: [-60, 0], ArrowUp: [0, 60], ArrowDown: [0, -60] }[e.key];
      if (d) { x += d[0]; y += d[1]; draw(); }
      else if (e.key === '+' || e.key === '=') zoomMid(1.5);
      else if (e.key === '-') zoomMid(1 / 1.5);
      else if (e.key === '0') fit();
      else return;
      e.preventDefault();
    });
    new ResizeObserver(() => { if (thing) fit(); }).observe(stage);
  };

  const zoomAt = (f, cx, cy) => {
    const r = stage.getBoundingClientRect(), px = cx - r.left, py = cy - r.top, n = Math.min(Math.max(k * f, fitK * .9), fitK * 24);
    x = px - (px - x) * n / k;
    y = py - (py - y) * n / k;
    k = n;
  };
  const zoomMid = f => { const r = stage.getBoundingClientRect(); zoomAt(f, r.left + r.width / 2, r.top + r.height / 2); draw(); };
  const draw = () => {
    const r = stage.getBoundingClientRect(), w = W * k, h = H * k, m = 60;
    x = w < r.width ? Math.min(Math.max(x, -m), r.width - w + m) : Math.min(Math.max(x, r.width - w - m), m);
    y = h < r.height ? Math.min(Math.max(y, -m), r.height - h + m) : Math.min(Math.max(y, r.height - h - m), m);
    thing.style.transform = `translate(${x}px,${y}px) scale(${k / crisp})`;
    clearTimeout(timer);
    timer = setTimeout(sharpen, 140);
  };
  /* once the finger stops, redraw the vector at its real size so small text is sharp */
  const sharpen = () => {
    if (!thing || pts.size) { if (thing) timer = setTimeout(sharpen, 140); return; }
    crisp = k;
    thing.style.width = W * k + 'px';
    thing.style.height = H * k + 'px';
    thing.style.transform = `translate(${x}px,${y}px)`;
  };
  const fit = () => {
    const r = stage.getBoundingClientRect();
    fitK = k = Math.min((r.width - 16) / W, (r.height - 16) / H);
    x = (r.width - W * k) / 2;
    y = (r.height - H * k) / 2;
    sharpen();
  };
  const put = (node, w, h) => {
    thing = node; W = w; H = h; crisp = 1;
    node.classList.add('vthing');
    stage.replaceChildren(node);
    fit();
  };

  const open = (name, sheets, pdfUrl, start = 0) => {
    if (!dlg) build();
    title.textContent = name;
    pdf.hidden = !pdfUrl;
    if (pdfUrl) pdf.href = pdfUrl;
    const show = i => {
      [...tabs.children].forEach((t, n) => t.setAttribute('aria-pressed', n === i));
      const s = sheets[i];
      if (s.node) { const c = s.node.cloneNode(true); c.innerHTML = c.innerHTML.replace(/(id="|url\(#)/g, '$1z'); c.removeAttribute('class'); c.removeAttribute('aria-hidden'); put(c, s.w, s.h); return; }
      const im = new Image();
      im.alt = `${name}, ${s.label}`;
      im.draggable = false;
      stage.classList.add('busy');
      im.onload = im.onerror = () => stage.classList.remove('busy');
      im.src = s.src;
      put(im, s.w, s.h);
    };
    tabs.replaceChildren(...(sheets.length > 1 ? sheets.map((s, i) => btn(s.label, s.label, () => show(i))) : []));
    document.documentElement.classList.add('locked');
    dlg.showModal();
    pushBack(() => dlg.close());
    show(start);
    stage.focus();
  };

  document.addEventListener('click', e => {
    const s = e.target.closest('[data-sheets]');
    if (s) {
      e.preventDefault();
      const n = +s.dataset.sheets, id = s.dataset.id, names = (s.dataset.labels || 'Main sheet|Connectors').split('|');
      open(s.dataset.title, Array.from({ length: n }, (_, i) => ({ src: `${base}sch/${id}-${i + 1}.svg`, label: names[i] || 'Sheet ' + (i + 1), w: 1123, h: 794 })), s.href || s.dataset.pdf || null, +s.dataset.start || 0);
      return;
    }
    const d = e.target.closest('[data-diagram]');
    if (d) {
      const fig = document.getElementById(d.dataset.diagram), v = $(innerWidth > innerHeight ? 'svg.wide' : 'svg.tall', fig);
      open(fig.dataset.title, [{ node: v, w: v.viewBox.baseVal.width, h: v.viewBox.baseVal.height }], null);
    }
  });

  /* ---------- rotatable boards ---------- */
  const calm = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let lib;
  const library = () => {
    if (!lib) {
      self.ModelViewerElement = Object.assign(self.ModelViewerElement || {}, { meshoptDecoderLocation: base + 'vendor/meshopt_decoder.js' });
      lib = import(base + 'vendor/model-viewer.min.js');
    }
    return lib;
  };
  $$('.model').forEach(box => {
    const go = $('.mgo', box), img = $('img', box), src = box.dataset.glb;
    let mv;
    const note = t => { go.hidden = false; $('span', go).textContent = t; };
    const start = async () => {
      if (mv) return;
      go.disabled = true;
      note('Loading…');
      try {
        await library();
        mv = document.createElement('model-viewer');
        Object.entries({
          src, 'camera-controls': '', 'touch-action': 'pan-y', 'shadow-intensity': '0.9', 'environment-image': 'neutral', exposure: '1.05',
          'camera-orbit': box.dataset.orbit || '-32deg 55deg 82%', 'min-camera-orbit': 'auto 0deg auto', 'max-camera-orbit': 'auto 180deg auto',
          'interaction-prompt': 'none', 'interpolation-decay': '90', 'alt': img.alt.replace('Render of', 'Rotatable model of'), loading: 'eager'
        }).forEach(([a, b]) => mv.setAttribute(a, b));
        if (!calm) { mv.setAttribute('auto-rotate', ''); mv.setAttribute('auto-rotate-delay', '2500'); mv.setAttribute('rotation-per-second', '10deg'); }
        mv.addEventListener('progress', e => { if (!mv.loaded) note(`Loading ${Math.round(e.detail.totalProgress * 100)}%`); });
        mv.addEventListener('load', () => { box.classList.add('live'); go.hidden = true; }, { once: true });
        mv.addEventListener('error', fail, { once: true });
        box.prepend(mv);
      } catch (err) { fail(); }
    };
    const fail = () => {
      if (mv) mv.remove();
      mv = null;
      go.disabled = false;
      note('3D not available here. Try again');
    };
    go.addEventListener('click', start);

    const full = btn('Full screen', '⤢ Full screen', () => (box.classList.contains('full') ? leave() : enter()));
    full.className = 'mfull';
    const reset = btn('Reset view', 'Reset', () => { mv.cameraOrbit = box.dataset.orbit || '-32deg 55deg 82%'; mv.cameraTarget = 'auto auto auto'; mv.fieldOfView = 'auto'; mv.resetTurntableRotation(0); });
    const flip = btn('Turn over', 'Turn over', () => { const o = mv.getCameraOrbit(), under = o.phi > Math.PI / 2; mv.cameraOrbit = `${o.theta}rad ${under ? 55 : 130}deg 82%`; });
    const tools = el('div', 'mtools');
    tools.append(flip, reset, full);
    box.append(tools);
    const enter = () => {
      box.classList.add('full');
      document.documentElement.classList.add('locked');
      mv.setAttribute('touch-action', 'none');
      const o = mv.getCameraOrbit();
      mv.cameraOrbit = `${o.theta}rad ${o.phi}rad 105%`;
      full.textContent = '✕ Close';
      full.setAttribute('aria-label', 'Close full screen');
      full.focus();
      pushBack(exit);
    };
    const exit = () => {
      box.classList.remove('full');
      document.documentElement.classList.remove('locked');
      mv.setAttribute('touch-action', 'pan-y');
      full.textContent = '⤢ Full screen';
      full.setAttribute('aria-label', 'Full screen');
    };
    const leave = () => { exit(); popBack(); };
    addEventListener('keydown', e => { if (e.key === 'Escape' && box.classList.contains('full')) leave(); });

    /* a mouse usually means a fast connection: load straight away. Phones wait for a tap. */
    const saver = navigator.connection && navigator.connection.saveData;
    if (matchMedia('(hover: hover) and (pointer: fine)').matches && !saver) start();
  });
})();
