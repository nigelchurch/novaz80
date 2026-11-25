/* Finger gestures. Everything here is an extra: without it the pages simply scroll. */
(() => {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const calm = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const glide = calm ? 'instant' : 'smooth';

  /* ---- story: swipe chapters like brochure pages ---- */
  const pager = $('.pager');
  if (pager) {
    const strip = $('.years'), list = $('ul', strip), links = $$('a', strip), pages = $$('.chapter', pager);
    const mode = matchMedia('(max-width:900px)'), root = document.documentElement;
    const name = i => links[i].textContent;
    let at = 0, touching = false, timer = 0, queued = false;

    const mark = i => links.forEach((a, n) => {
      if (n === i) {
        a.setAttribute('aria-current', 'true');
        list.scrollTo({ left: a.offsetLeft - list.clientWidth / 2 + a.offsetWidth / 2, behavior: glide });
      } else a.removeAttribute('aria-current');
    });

    pages.forEach((p, i) => {
      const bar = document.createElement('div');
      bar.className = 'turn';
      const prev = document.createElement('button'), count = document.createElement('span'), next = document.createElement('button');
      prev.type = next.type = 'button';
      if (i) { prev.textContent = '← ' + name(i - 1); prev.addEventListener('click', () => go(i - 1)); } else prev.hidden = true;
      count.textContent = i ? `${i + 1} / ${pages.length}` : 'Swipe to turn the page';
      if (i < pages.length - 1) { next.textContent = name(i + 1) + ' →'; next.addEventListener('click', () => go(i + 1)); }
      else { next.textContent = 'Build ↓'; next.addEventListener('click', () => $('#build').scrollIntoView({ behavior: glide })); }
      bar.append(prev, count, next);
      p.append(bar);
    });

    const head = () => strip.offsetHeight + (parseFloat(getComputedStyle(strip).top) || 0);
    const top = () => pager.getBoundingClientRect().top + scrollY - head();
    const depth = () => Math.max(0, scrollY - top());
    const on = () => root.classList.contains('swipe');
    const size = h => { pager.style.height = h + 'px'; };

    /* waiting pages slide down to wherever the reader is, so a swipe always reveals a heading */
    const sink = () => { if (on()) pager.style.setProperty('--off', depth() + 'px'); };

    const settle = () => {
      clearTimeout(timer);
      if (!on() || touching) return;
      const i = Math.max(0, Math.min(pages.length - 1, Math.round(pager.scrollLeft / pager.clientWidth)));
      const moved = i !== at, deep = depth() > 0;
      at = i;
      pages.forEach((p, n) => p.classList.toggle('here', n === i));
      size(pages[i].offsetHeight);
      if (moved && deep) scrollTo({ top: top(), behavior: 'instant' });
      sink();
      mark(i);
    };

    const go = (i, how = glide) => {
      if (Math.abs(i - at) > 1) how = 'instant';
      pager.scrollTo({ left: i * pager.clientWidth, behavior: how });
      if (how === 'instant') settle();
      else grow();
    };

    const grow = () => size(Math.max(pages[at].offsetHeight, depth() + Math.max(innerHeight, 300)));

    pager.addEventListener('scroll', () => {
      if (!on()) return;
      if (Math.abs(pager.scrollLeft - at * pager.clientWidth) > 4) grow();
      clearTimeout(timer);
      timer = setTimeout(settle, 160);
    }, { passive: true });
    pager.addEventListener('scrollend', settle);
    pager.addEventListener('touchstart', () => { touching = true; sink(); }, { passive: true });
    ['touchend', 'touchcancel'].forEach(t => pager.addEventListener(t, e => {
      touching = e.touches.length > 0;
      clearTimeout(timer);
      timer = setTimeout(settle, 160);
    }, { passive: true }));
    addEventListener('scroll', () => {
      if (queued) return;
      queued = true;
      requestAnimationFrame(() => { queued = false; sink(); });
    }, { passive: true });

    const target = h => pages.findIndex(p => h.length > 1 && '#' + p.id === h);
    document.addEventListener('click', e => {
      const a = e.target.closest('a[href^="#"]');
      if (!a || !on()) return;
      const i = target(a.hash);
      if (i < 0) return;
      e.preventDefault();
      history.replaceState(null, '', a.hash);
      const deep = depth() > 0;
      go(i);
      if (!deep) scrollTo({ top: top(), behavior: glide });
    });
    pager.addEventListener('keydown', e => {
      if (!on() || e.target.closest('input')) return;
      if (e.key === 'ArrowRight' && at < pages.length - 1) { e.preventDefault(); go(at + 1); }
      if (e.key === 'ArrowLeft' && at) { e.preventDefault(); go(at - 1); }
    });

    const apply = () => {
      root.classList.toggle('swipe', mode.matches);
      if (mode.matches) {
        pager.scrollTo({ left: at * pager.clientWidth, behavior: 'instant' });
        settle();
      } else {
        pager.style.height = '';
        links.forEach(a => a.removeAttribute('aria-current'));
      }
    };
    new ResizeObserver(() => { if (on() && !touching && Math.abs(pager.scrollLeft - at * pager.clientWidth) < 4) size(pages[at].offsetHeight); }).observe(pager);
    const ro = new ResizeObserver(() => { if (on() && !touching) size(pages[at].offsetHeight); });
    pages.forEach(p => ro.observe(p));
    let width = innerWidth;
    addEventListener('resize', () => { if (innerWidth !== width) { width = innerWidth; apply(); } });
    const first = target(location.hash);
    if (first > 0) at = first;
    apply();
    if (first > 0 && mode.matches) requestAnimationFrame(() => scrollTo({ top: top(), behavior: 'instant' }));
  }

  /* ---- carousels: native snapping, plus dots that follow ---- */
  $$('.cards, .sec .pair, .phases, .machines').forEach(box => {
    const dots = document.createElement('div');
    dots.className = 'dots';
    dots.setAttribute('aria-hidden', 'true');
    const items = [...box.children];
    items.forEach(() => dots.append(document.createElement('i')));
    box.after(dots);
    const upd = () => {
      const end = box.scrollLeft + box.clientWidth >= box.scrollWidth - 4;
      const step = items[1].offsetLeft - items[0].offsetLeft || 1;
      const n = end && box.scrollLeft > 0 ? items.length - 1 : Math.round(box.scrollLeft / step);
      [...dots.children].forEach((d, i) => d.classList.toggle('on', i === n));
    };
    box.addEventListener('scroll', upd, { passive: true });
    upd();
  });

  /* ---- one-finger horizontal drag, leaving vertical scrolling alone ---- */
  const drag = (el, { skip, move, done }) => {
    let x, y, lock, t;
    const reset = () => { x = null; lock = null; };
    reset();
    el.addEventListener('touchstart', e => {
      reset();
      const p = e.touches[0];
      if (e.touches.length > 1 || (skip && e.target.closest(skip)) || p.clientX < 24 || p.clientX > innerWidth - 24) return;
      x = p.clientX; y = p.clientY; t = e.timeStamp;
    }, { passive: true });
    el.addEventListener('touchmove', e => {
      if (x === null) return;
      if (e.touches.length > 1) { if (lock === 'x') done(0, 1); return reset(); }
      const dx = e.touches[0].clientX - x, dy = e.touches[0].clientY - y;
      if (!lock && Math.hypot(dx, dy) > 10) lock = Math.abs(dx) > Math.abs(dy) * 1.4 ? 'x' : 'y';
      if (lock === 'x') move(dx);
    }, { passive: true });
    el.addEventListener('touchend', e => {
      if (x !== null && lock === 'x') done(e.changedTouches[0].clientX - x, e.timeStamp - t);
      reset();
    }, { passive: true });
    el.addEventListener('touchcancel', () => { if (lock === 'x') done(0, 1); reset(); }, { passive: true });
  };
  const flick = (dx, ms) => Math.abs(dx) > 90 || (Math.abs(dx) > 35 && Math.abs(dx) / ms > .45);

  /* ---- builder: swipe the stack to change processor, pinch to pull it apart ---- */
  const form = $('#builder');
  if (form) {
    const box = $('.stagebox'), stage = $('#stage'), cpus = $$('input[name=cpu]', form);
    const dots = document.createElement('div');
    dots.className = 'dots cpu';
    dots.setAttribute('aria-hidden', 'true');
    cpus.forEach(() => dots.append(document.createElement('i')));
    box.append(dots);
    const upd = () => [...dots.children].forEach((d, i) => d.classList.toggle('on', cpus[i].checked));
    form.addEventListener('change', upd);
    upd();
    const slide = (x, ms) => { stage.style.transition = ms ? `transform ${ms}ms ease-out, opacity ${ms}ms` : ''; stage.style.transform = x ? `translateX(${x}px)` : ''; };
    drag(box, {
      move: dx => slide(dx * .6),
      done: (dx, ms) => {
        const i = cpus.findIndex(c => c.checked), n = (i + (dx < 0 ? 1 : -1) + cpus.length) % cpus.length;
        if (!flick(dx, ms)) return slide(0, 200);
        const swap = () => { cpus[n].checked = true; cpus[n].dispatchEvent(new Event('change', { bubbles: true })); };
        if (calm) { swap(); return slide(0); }
        const away = Math.sign(dx) * 160;
        slide(away, 140);
        stage.style.opacity = 0;
        setTimeout(() => {
          swap();
          slide(-away);
          void stage.offsetWidth;
          slide(0, 220);
          stage.style.opacity = '';
        }, 140);
      }
    });
    let d0 = 0, g0 = 0;
    const span = e => Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY);
    box.addEventListener('touchstart', e => { if (e.touches.length === 2) { d0 = span(e); g0 = +form.gap.value; } }, { passive: true });
    box.addEventListener('touchmove', e => {
      if (e.touches.length !== 2 || !d0) return;
      e.preventDefault();
      form.gap.value = g0 + (span(e) / d0 - 1) * 16;
      form.gap.dispatchEvent(new Event('input', { bubbles: true }));
    }, { passive: false });
    box.addEventListener('touchend', e => { if (e.touches.length < 2) d0 = 0; }, { passive: true });
  }

  /* ---- board pages: swipe to the next board ---- */
  const prev = $('a[rel=prev]'), next = $('a[rel=next]'), main = $('main');
  if (prev && next) {
    try {
      const from = sessionStorage.getItem('nz-from');
      sessionStorage.removeItem('nz-from');
      if (from && !calm) main.classList.add(from);
    } catch { /* storage blocked: no entrance animation */ }
    const pull = (x, ms) => { main.style.transition = ms ? `transform ${ms}ms ease-out` : ''; main.style.transform = x ? `translateX(${x}px)` : ''; };
    drag(main, {
      skip: '.scroll, pre, .pair, input, .seg, .model, .viewer',
      move: dx => pull(dx * .45),
      done: (dx, ms) => {
        if (!flick(dx, ms) || Math.abs(dx) < 60) return pull(0, 220);
        const a = dx < 0 ? next : prev;
        try { sessionStorage.setItem('nz-from', dx < 0 ? 'from-right' : 'from-left'); } catch { /* fine */ }
        pull(Math.sign(dx) * innerWidth, calm ? 0 : 180);
        setTimeout(() => { location.href = a.href; }, calm ? 0 : 150);
      }
    });
    addEventListener('pageshow', e => { if (e.persisted) pull(0); });
  }
})();
