(() => {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const calm = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* build your machine */
  const form = $('#builder');
  if (form) {
    const stage = $('#stage'), out = $('#readout'), small = matchMedia('(max-width:640px)');
    const fit = () => { form.gap.max = small.matches ? 24 : 34; stage.style.setProperty('--gap', form.gap.value); };
    small.addEventListener('change', fit);
    fit();
    const CPU = {
      z80: { name: 'Z80 SBC', rows: [['Processor', 'Z80 at 4 MHz'], ['Memory', '32 K ROM, 32 K RAM'], ['On board', 'PIO and CTC']] },
      '6502': { name: '6502 SBC', rows: [['Processor', 'W65C02S at 1 MHz'], ['Memory', '32 K ROM, just under 32 K RAM'], ['On board', 'VIA']] },
      mtx: { name: 'Memotech MTX512 equivalent', rows: [['Processor', 'Z80 at 4 MHz, clocked by the video board'], ['Memory', '32 K ROM in four 8 K blocks, 64 K RAM'], ['On board', 'MTX page register']] }
    };
    const OPT = { pr1: 'in-circuit programming', vdp: 'TMS99xx video, SN76489 sound', io1: 'serial, timers, parallel I/O, keyboard', io2: 'LCD, 8 buttons, 82C55 ports' };
    const ALT = { pr1: 'Fast programmer', vdp: 'Video and sound board', io1: 'I/O board', io2: 'LCD board' };
    const draw = () => {
      const cpu = form.cpu.value, need = cpu === 'mtx';
      ['vdp', 'io1'].forEach(k => { const c = form.elements[k]; if (need) c.checked = true; c.disabled = need; });
      const on = k => form.elements[k].checked;
      const list = [on('pr1') && 'pr1', cpu, on('vdp') && 'vdp', on('io1') && 'io1', on('io2') && 'io2'].filter(Boolean);
      stage.style.setProperty('--n', list.length);
      stage.style.setProperty('--gap', form.gap.value);
      $('.deck', stage).replaceChildren(...list.map((k, i) => {
        const im = new Image(1300, 850);
        im.src = `assets/img/iso-${k}.webp`;
        im.alt = k === cpu ? CPU[cpu].name + ' board' : ALT[k];
        im.style.setProperty('--i', i);
        return im;
      }));
      const extra = list.filter(k => OPT[k]).map(k => OPT[k]).join('; ') || 'Nothing: it is a complete computer on its own';
      out.replaceChildren(...[['Machine', CPU[cpu].name], ...CPU[cpu].rows, ['Added', extra]].map(([a, b]) => {
        const d = document.createElement('div'), t = document.createElement('dt'), v = document.createElement('dd');
        t.textContent = a; v.textContent = b; d.append(t, v);
        return d;
      }));
      $('#need').hidden = !need;
      $('#mname').textContent = CPU[cpu].name;
    };
    form.addEventListener('change', e => { if (e.target.id !== 'gap') draw(); });
    form.gap.addEventListener('input', () => stage.style.setProperty('--gap', form.gap.value));
    form.addEventListener('submit', e => e.preventDefault());
    draw();
  }

  /* upload replay */
  const term = $('#term');
  if (term) {
    const full = term.innerHTML, lines = full.split('\n'), btn = $('#replay');
    let run = 0;
    const play = async () => {
      const me = ++run, wait = ms => new Promise(r => setTimeout(r, ms));
      term.innerHTML = '';
      let done = '';
      for (const l of lines) {
        const m = l.match(/^<span class="o">(#+)<\/span>$/);
        if (m) for (let i = 1; i <= m[1].length; i += 2) {
          await wait(45); if (me !== run) return;
          term.innerHTML = done + `<span class="o">${'#'.repeat(i)}</span>`;
        }
        done += l + '\n';
        term.innerHTML = done;
        await wait(l.trim() ? 170 : 40); if (me !== run) return;
      }
      term.innerHTML = full;
    };
    btn.hidden = false;
    btn.addEventListener('click', play);
    if (!calm && 'IntersectionObserver' in window) {
      const io = new IntersectionObserver(e => { if (e[0].isIntersecting) { io.disconnect(); play(); } }, { threshold: .5 });
      io.observe(term);
    }
  }

  /* bus explorer */
  const pins = $('#pins');
  if (pins) {
    const addr = a => a.map(n => ['A' + n, 'Address line ' + n]);
    const BUS = {
      ADDR: ['Low address byte', addr([0, 1, 2, 3, 4, 5, 6, 7])],
      ADDR2: ['High address byte, in reverse order', addr([15, 14, 13, 12, 11, 10, 9, 8])],
      SPEC: ['Power, clocks and interrupt chain', [['GND', 'Ground'], ['+5V', 'Stack supply, made on the CPU board'], ['VDPINTB', 'Video interrupt, to the I/O board timer'], ['IEO1', 'Interrupt daisy chain'], ['IEO2', 'Interrupt daisy chain'], ['4M', '4 MHz clock from the video board'], ['OUT0', 'Write strobe for port 00h'], ['KBDRST', 'Keyboard reset']]],
      PROG: ['The in-circuit programmer', [['SP3', 'Spare'], ['ROM7', 'Cartridge ROM select (MTX)'], ['BUSRQ', 'Take the bus from the CPU'], ['ROMWEX', 'ROM write enable'], ['ROMCSX', 'ROM select'], ['RESX', 'Reset the target'], ['ROMOEX', 'ROM output enable'], ['PWR', 'Raw DC input']]],
      DATA: ['Data bus', [0, 1, 2, 3, 4, 5, 6, 7].map(n => ['D' + n, 'Data line ' + n])],
      AUX: ['Spare lines and SPI', [['–', 'Spare'], ['–', 'Spare'], ['MISO', 'SPI'], ['MOSI', 'SPI'], ['SCK', 'SPI'], ['–', 'Spare'], ['–', 'Spare'], ['–', 'Spare']]],
      CTRL: ['Z80-style control', [['RSTB', 'Reset'], ['CLK', 'Clock'], ['M1B', 'Opcode fetch'], ['MREQB', 'Memory request'], ['IORQB', 'I/O request'], ['RDB', 'Read'], ['WRB', 'Write'], ['INTB', 'Interrupt']]],
      MTX: ['The MTX page register', [['P0', 'RAM page'], ['P1', 'RAM page'], ['P2', 'RAM page'], ['P3', 'RAM page'], ['R0', 'ROM page'], ['R1', 'ROM page'], ['R2', 'ROM page'], ['CPM', 'All-RAM mode']]]
    };
    const bs = $$('.board > button');
    const show = k => {
      bs.forEach(b => b.setAttribute('aria-pressed', b.dataset.g === k));
      $('#busname').textContent = k;
      $('#busrole').textContent = BUS[k][0];
      pins.replaceChildren(...BUS[k][1].map(([a, t], i) => {
        const li = document.createElement('li');
        li.innerHTML = `<i>${i + 1}</i><b>${a}</b><span>${t}</span>`;
        return li;
      }));
    };
    bs.forEach(b => b.addEventListener('click', () => show(b.dataset.g)));
    show('CTRL');
  }

  /* board maps */
  const map = $('.map');
  if (map) {
    const all = $$('[data-p]', map);
    const pick = n => all.forEach(e => e.classList.toggle('on', e.dataset.p === n));
    all.forEach(e => ['click', 'mouseenter', 'focus'].forEach(t => e.addEventListener(t, () => pick(e.dataset.p))));
  }

  /* MTX paging, straight from the memory-map logic */
  const pg = $('#paging');
  if (pg) {
    const draw = () => {
      const R = +pg.r.value, P = +pg.p.value, C = pg.cpm.checked, x = !C && R === 6;
      const none = ['none', 'Nothing selected, reads 00h'];
      const page = { 0: ['rom', 'ROM B, BASIC'], 1: ['rom', 'ROM C'], 3: ['ext', 'Spare 8 K block'], 6: ['ext', 'ROMx expansion'], 7: ['ext', 'Off-board cartridge'] };
      const m = [
        ['0000', '1FFF', C ? (P === 0 ? ['ram', 'RAM2'] : none) : ['rom', 'ROM A, operating system']],
        ['2000', '3FFF', C ? (P === 0 ? ['ram', 'RAM2'] : none) : page[R] || none],
        ['4000', '7FFF', x ? ['ext', 'ROMx expansion'] : P === 0 && R !== 6 ? ['ram', 'RAM2'] : none],
        ['8000', 'BFFF', P === 0 ? ['ram', 'RAM'] : P === 1 && !C ? ['ram', 'RAM2'] : none],
        ['C000', 'FFFF', ['ram', 'RAM, always present']]
      ];
      $('#mem').replaceChildren(...m.map(([a, b, [c, t]]) => {
        const li = document.createElement('li');
        li.className = c;
        li.innerHTML = `<b>${t}</b><code>${a}–${b}</code>`;
        return li;
      }));
      const v = (C ? 128 : 0) + R * 16 + P;
      $('#outv').textContent = `OUT (00h), ${v.toString(16).toUpperCase().padStart(2, '0')}h`;
    };
    pg.addEventListener('change', draw);
    draw();
  }
})();
