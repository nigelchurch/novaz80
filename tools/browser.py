"""Browser checks in installed Edge. Run: python tools/browser.py --check
Screenshots go to tools/shots (or --out DIR)."""
import argparse
import glob
import http.server
import os
import re
import sys
import tempfile
import threading
from functools import partial

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZES = {"desktop": (1440, 900), "fold7-inner": (750, 832), "fold7-outer": (411, 960), "fold5-outer": (344, 882),
         "small-320": (320, 640), "landscape": (882, 344)}


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "shots"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}/"
    pages = ["index.html", "credits.html", "design.html"] + sorted("boards/" + os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "boards", "*.html")))
    bad = []
    with sync_playwright() as p, tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as prof:
        ctx = p.chromium.launch_persistent_context(prof, channel="msedge", headless=True)
        pg = ctx.pages[0]
        cur = [""]

        def note(kind, text):
            bad.append(f"{cur[0]}: {kind}: {text}")

        pg.on("console", lambda m: m.type in ("error", "warning") and note("console " + m.type, m.text))
        pg.on("pageerror", lambda e: note("page error", str(e)))
        pg.on("response", lambda r: r.status >= 400 and note("http", f"{r.status} {r.url}"))
        cdp = ctx.new_cdp_session(pg)
        cdp.send("Log.enable")
        cdp.send("Audits.enable")
        cdp.on("Log.entryAdded", lambda e: e["entry"]["level"] in ("error", "warning") and note("log", e["entry"]["text"]))
        cdp.on("Audits.issueAdded", lambda e: note("issue", str(e["issue"]["code"]) + " " + str(e["issue"]["details"])[:300]))
        links = set()
        for size, (w, h) in SIZES.items():
            pg.set_viewport_size({"width": w, "height": h})
            for u in pages:
                cur[0] = f"{size} {u}"
                pg.goto(base + u, wait_until="load")
                if size == "desktop":
                    for x in pg.eval_on_selector_all("a[href]", "e=>e.map(a=>a.href)"):
                        links.add(x)
                    src = open(os.path.join(ROOT, u), encoding="utf8").read()
                    if "apple-mobile-web-app-capable" in src and '"mobile-web-app-capable"' not in src:
                        note("lint", "deprecated apple-mobile-web-app-capable")
                    if re.search(r"<(center|font|marquee)\b", src):
                        note("lint", "deprecated tag")
                    dup = pg.evaluate("()=>{const i=[...document.querySelectorAll('[id]')].map(e=>e.id);return i.filter((x,n)=>i.indexOf(x)!==n)}")
                    if dup:
                        note("lint", f"duplicate ids {dup}")
                    for m in pg.eval_on_selector_all("img:not([alt])", "e=>e.map(i=>i.src)"):
                        note("lint", "img without alt " + m)
                over = pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
                if over > 0:
                    note("layout", f"page scrolls sideways by {over}px")
                if w <= 900:
                    tiny = pg.evaluate("""()=>[...document.querySelectorAll('a,button,summary,input')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&!e.closest('p,figcaption,dd,.notes,.map .inner')&&!e.matches('.skip,.pick input')&&(r.height<43.5||r.width<36)}).map(e=>(e.textContent.trim()||e.name)+' '+Math.round(e.getBoundingClientRect().width)+'x'+Math.round(e.getBoundingClientRect().height))""")
                    if tiny:
                        note("tap target", str(tiny))
                pg.evaluate("document.querySelectorAll('img[loading]').forEach(i=>i.loading='eager')")
                pg.wait_for_function("[...document.images].every(i=>i.complete)")
                for m in pg.eval_on_selector_all("img", "e=>e.filter(i=>!i.naturalWidth).map(i=>i.src)"):
                    note("image", "broken " + m)
                if u in ("index.html", "credits.html", "design.html", "boards/mtx.html", "boards/z80.html", "boards/6502.html", "boards/pr2.html", "boards/io1-notes.html"):
                    pg.wait_for_timeout(1700)
                    pg.screenshot(path=os.path.join(a.out, f"{size}-{u.replace('/', '-')[:-5]}.png"), full_page=True, animations="disabled")
        # links
        for x in sorted(links):
            if not x.startswith(base):
                continue
            path, _, frag = x[len(base):].partition("#")
            f = os.path.join(ROOT, path or "index.html")
            cur[0] = "links"
            if not os.path.isfile(f):
                note("link", "missing " + x)
            elif frag and f.endswith(".html") and f'id="{frag}"' not in open(f, encoding="utf8").read():
                note("link", "no anchor " + x)
        # behaviour
        pg.set_viewport_size({"width": 1440, "height": 900})
        cur[0] = "behaviour"

        def ok(name, cond):
            if not cond:
                note("behaviour", name)

        pg.goto(base + "index.html")
        n = lambda: pg.locator("#stage img").count()
        ok("builder starts with 3 boards", n() == 3)
        pg.check("input[name=cpu][value='6502']", force=True)
        ok("6502 readout", "W65C02S" in pg.inner_text("#readout"))
        pg.uncheck("input[name=vdp]", force=True)
        ok("removing video leaves 2 boards", n() == 2)
        pg.check("input[name=cpu][value=mtx]", force=True)
        ok("MTX forces video and I/O on", n() == 3 and pg.is_disabled("input[name=vdp]") and pg.is_visible("#need"))
        pg.check("input[name=cpu][value=z80]", force=True)
        ok("options unlock after MTX", pg.is_enabled("input[name=vdp]"))
        pg.check("input[name=io2]", force=True)
        pg.check("input[name=pr1]", force=True)
        ok("all five boards", n() == 5)
        pg.click("[data-g=MTX]")
        ok("bus explorer", "CPM" in pg.inner_text("#pins") and pg.locator("#pins li").count() == 8)
        pg.evaluate("document.querySelector('#term').scrollIntoView({block:'center'})")
        pg.wait_for_function("document.querySelector('#term').textContent.length<200")
        pg.wait_for_function("document.querySelector('#term').textContent.includes('17.703169')", timeout=30000)
        pg.goto(base + "boards/mtx.html")
        mem = lambda: pg.inner_text("#mem")
        ok("MTX reset map", "BASIC" in mem() and "ROM A" in mem())
        pg.check("input[name=r][value='6']", force=True)
        ok("R=6 gives ROMx twice", mem().count("ROMx") == 2)
        pg.check("input[name=cpm]", force=True)
        ok("CPM+R6 fault shown", mem().count("Nothing") == 1 and "E0h" in pg.inner_text("#outv"))
        pg.check("input[name=r][value='0']", force=True)
        ok("CPM all RAM", "ROM " not in mem() and "Nothing" not in mem())
        pg.goto(base + "boards/z80.html")
        pg.click(".plist button >> nth=2")
        ok("parts map highlights", pg.locator(".spot.on").inner_text() == "3")
        # phone behaviour
        for pw, ph in ((411, 960), (344, 882)):
            pg.set_viewport_size({"width": pw, "height": ph})
            pg.goto(base + "index.html")
            box = lambda s: pg.locator(s).bounding_box()
            nb = box(".nav ul")
            ok(f"{pw} menu at the bottom", abs(nb["y"] + nb["height"] - ph) < 2)
            pg.evaluate("document.querySelector('#readout').scrollIntoView({block:'end',behavior:'instant'})")
            pg.wait_for_timeout(300)
            s = box(".stagebox")
            ok(f"{pw} stack pinned while choosing", -1 <= s["y"] < 5)
            y0 = box("#gap")["y"]
            pg.check("input[name=io2]", force=True)
            pg.check("input[name=pr1]", force=True)
            pg.evaluate("()=>{const e=document.querySelector('#gap');e.value=e.max;e.dispatchEvent(new Event('input',{bubbles:true}))}")
            pg.wait_for_timeout(300)
            top = pg.evaluate("Math.min(...[...document.querySelectorAll('#stage img')].map(i=>i.getBoundingClientRect().top))")
            ok(f"{pw} exploded stack stays on screen ({top:.0f})", top >= -30)
            pg.evaluate("document.querySelector('#nov').scrollIntoView({behavior:'instant'})")
            pg.wait_for_timeout(900)
            ok(f"{pw} year strip follows", pg.inner_text(".years [aria-current]") == "MTX512")
            pg.goto(base + "boards/io1.html")
            pg.locator(".plist button").last.scroll_into_view_if_needed()
            pg.wait_for_timeout(300)
            m = box(".map .pic")
            ok(f"{pw} board picture pinned ({m['y']:.0f})", m["y"] > -m["height"] / 2)
        # swiping, with synthetic touches
        tc = ctx.new_cdp_session(pg)
        tc.send("Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 2})

        def swipe(x0, x1, y, steps=8, y1=None):
            y1 = y if y1 is None else y1
            tc.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y}]})
            for k in range(1, steps + 1):
                tc.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x0 + (x1 - x0) * k / steps, "y": y + (y1 - y) * k / steps}]})
                pg.wait_for_timeout(16)
            tc.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
            pg.wait_for_timeout(1100)

        cur_year = lambda: pg.evaluate("(document.querySelector('.years [aria-current]')||{}).textContent||''")
        for pw, ph in ((411, 960), (344, 882), (750, 832)):
            pg.set_viewport_size({"width": pw, "height": ph})
            pg.goto(base + "index.html")
            pg.evaluate("window.scrollTo({top:document.querySelector('.pager').getBoundingClientRect().top+scrollY+300,behavior:'instant'})")
            pg.wait_for_timeout(300)
            swipe(pw * .85, pw * .15, ph * .6)
            ok(f"{pw} swipe left goes to Ben Eater (got {cur_year()})", cur_year() == "Ben Eater")
            hy = pg.evaluate("document.querySelector('#spark h2').getBoundingClientRect().top")
            ok(f"{pw} next page opens at its heading ({hy:.0f})", 0 < hy < ph * .4)
            swipe(pw * .15, pw * .85, ph * .6)
            ok(f"{pw} swipe right goes back (got {cur_year()})", cur_year() == "1983")
            if "index.html" not in pg.url:
                note("behaviour", "swipe left the page")
                continue
            y0 = pg.evaluate("scrollY")
            swipe(pw * .5, pw * .48, ph * .75, y1=ph * .35)
            ok(f"{pw} vertical drag still scrolls", pg.evaluate("scrollY") > y0 + 80 and cur_year() == "1983")
            pg.click(".years a:has-text('MTX512')")
            pg.wait_for_timeout(700)
            hp = pg.evaluate("[document.querySelector('.pager').offsetHeight,document.querySelector('#nov').offsetHeight]")
            ok(f"{pw} year tap opens MTX512 at full height {hp}", cur_year() == "MTX512" and abs(hp[0] - hp[1]) < 2)
            pg.locator("#nov .turn button").last.click()
            pg.wait_for_timeout(1100)
            ok(f"{pw} next button", cur_year() == "Faster")
            pg.locator(".stagebox").scroll_into_view_if_needed()
            pg.wait_for_timeout(300)
            s = box(".stagebox")
            mid = min(max(s["y"] + s["height"] / 2, 120), ph - 120)
            swipe(s["x"] + s["width"] * .8, s["x"] + s["width"] * .25, mid)
            ok(f"{pw} swiping the stack picks the 6502", pg.is_checked("input[value='6502']"))
            cx = s["x"] + s["width"] / 2
            g = float(pg.input_value("#gap"))
            tc.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": cx - 25, "y": mid, "id": 0}, {"x": cx + 25, "y": mid, "id": 1}]})
            for k in range(1, 7):
                tc.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": cx - 25 - k * 8, "y": mid, "id": 0}, {"x": cx + 25 + k * 8, "y": mid, "id": 1}]})
                pg.wait_for_timeout(16)
            tc.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
            ok(f"{pw} pinch pulls the stack apart", float(pg.input_value("#gap")) > g + 3)
            pg.goto(base + "boards/z80.html")
            swipe(pw * .8, pw * .2, ph * .35)
            pg.wait_for_load_state()
            ok(f"{pw} board swipe goes to 6502 ({pg.url})", pg.url.endswith("/6502.html"))
            swipe(pw * .2, pw * .8, ph * .35)
            pg.wait_for_load_state()
            ok(f"{pw} board swipe goes back ({pg.url})", pg.url.endswith("/z80.html"))
            swipe(pw * .5, pw * .42, ph * .35)
            ok(f"{pw} small nudge stays put", pg.url.endswith("/z80.html") and pg.evaluate("document.querySelector('main').style.transform") == "")
        pg.set_viewport_size({"width": 411, "height": 960})
        pg.goto(base + "index.html#boards")
        pg.wait_for_timeout(500)
        pg.evaluate("document.querySelector('.cards').scrollIntoView({block:'center',behavior:'instant'})")
        pg.wait_for_timeout(900)
        cb = box(".cards")
        swipe(350, 90, cb["y"] + 120)
        ok("board carousel swipes and its dots follow", pg.evaluate("document.querySelector('.cards').scrollLeft>200&&!document.querySelector('#boards .dots i').classList.contains('on')"))
        pg.goto(base + "index.html#nov")
        pg.wait_for_timeout(600)
        ok("link straight to a chapter", cur_year() == "MTX512")
        pg.set_viewport_size({"width": 750, "height": 832})
        pg.wait_for_timeout(600)
        ok("unfolding keeps the chapter", cur_year() == "MTX512" and abs(pg.evaluate("document.querySelector('#nov').getBoundingClientRect().left")) < 2)
        pg.set_viewport_size({"width": 1200, "height": 800})
        pg.wait_for_timeout(400)
        ok("wide screens return to scrolling", pg.evaluate("getComputedStyle(document.querySelector('.pager')).display") == "block")
        # rotating boards, schematics and diagrams
        tc.send("Emulation.setTouchEmulationEnabled", {"enabled": False})
        pg.set_viewport_size({"width": 1440, "height": 900})
        cur[0] = "3D and schematics"
        ids = ["z80", "6502", "mtx", "io1", "vdp", "io2", "pr1", "pr2"]
        for i in ids:
            pg.goto(base + f"boards/{i}.html")
            pg.wait_for_selector(".model.live, .mgo:not([disabled])", timeout=90000)
            if not pg.locator(".model.live").count():
                pg.click(".mgo")
                pg.wait_for_selector(".model.live", timeout=90000)
            d = pg.evaluate("(()=>{const d=document.querySelector('model-viewer').getDimensions();return [d.x,d.y,d.z]})()")
            want = 0.33 if i == "pr2" else 0.12
            ok(f"{i} model is board-sized ({[round(v, 3) for v in d]})", 0.095 < d[0] < want and d[1] < 0.07)
            pg.locator(".sheet").last.click()
            pg.wait_for_function("(document.querySelector('.vthing')||{}).naturalWidth>0")
            ok(f"{i} schematic opens on the sheet tapped", f"sch/{i}-{pg.locator('.sheet').count()}.svg" in pg.get_attribute(".vthing", "src"))
            pg.keyboard.press("Escape")
            pg.wait_for_function("!document.querySelector('dialog[open]')&&!(history.state&&history.state.viewer)")
        pg.goto(base + "boards/z80.html")
        pg.wait_for_selector(".model.live", timeout=90000) if pg.evaluate("matchMedia('(hover: hover) and (pointer: fine)').matches") else (pg.click(".mgo"), pg.wait_for_selector(".model.live", timeout=90000))
        th = lambda: pg.evaluate("(()=>{const o=document.querySelector('model-viewer').getCameraOrbit();return [o.theta,o.phi]})()")
        m = box("model-viewer")
        o0 = th()
        pg.mouse.move(m["x"] + m["width"] / 2, m["y"] + m["height"] / 2)
        pg.mouse.down()
        pg.mouse.move(m["x"] + m["width"] / 2 + 160, m["y"] + m["height"] / 2 + 60, steps=10)
        pg.mouse.up()
        pg.wait_for_timeout(700)
        z = th()
        ok(f"dragging rotates the board {o0} {z}", abs(z[0] - o0[0]) > .3 and abs(z[1] - o0[1]) > .05)
        pg.click("text=Turn over")
        pg.wait_for_timeout(900)
        ok("turn over shows the underside", th()[1] > 1.7)
        pg.click(".mfull")
        pg.wait_for_timeout(400)
        ok("3D fills the screen", box(".model")["height"] > 890)
        pg.go_back()
        pg.wait_for_timeout(400)
        ok("Back leaves 3D full screen, not the page", pg.url.endswith("z80.html") and not pg.locator(".model.full").count())
        pg.click("text=See the schematic")
        pg.wait_for_timeout(600)
        w0 = box(".vthing")["width"]
        pg.click("[aria-label='Zoom in']")
        pg.click("[aria-label='Zoom in']")
        pg.wait_for_timeout(400)
        b1 = box(".vthing")
        ok("schematic zooms", b1["width"] > w0 * 2)
        pg.mouse.move(700, 450)
        pg.mouse.down()
        pg.mouse.move(600, 400, steps=5)
        pg.mouse.up()
        ok("schematic drags", abs(box(".vthing")["x"] - b1["x"]) > 60)
        pg.click(".vtabs button >> nth=1")
        pg.wait_for_timeout(500)
        ok("sheet tabs", "z80-2.svg" in pg.get_attribute(".vthing", "src"))
        pg.click("[aria-label=Close]")
        pg.wait_for_timeout(400)
        ok("schematic closes", not pg.locator("dialog[open]").count() and pg.url.endswith("z80.html"))
        pg.goto(base + "index.html")
        pg.click(".pick label >> nth=1")
        ok("diagram tabs", pg.is_visible("#d-flat") and not pg.is_visible("#d-stacked"))
        pg.click("#boards .jump a >> nth=2")
        pg.wait_for_timeout(500)
        ok("schematic chips on the main page", "mtx-1.svg" in pg.get_attribute(".vthing", "src"))
        pg.keyboard.press("Escape")
        pg.wait_for_function("!document.querySelector('dialog[open]')&&!(history.state&&history.state.viewer)")
        pg.goto(base + "design.html")
        for w, vis, hid in ((1440, "wide", "tall"), (411, "tall", "wide")):
            pg.set_viewport_size({"width": w, "height": 900})
            ok(f"{w} uses the {vis} diagrams", pg.is_visible(f"#d-flat svg.{vis}") and not pg.is_visible(f"#d-flat svg.{hid}"))
        pg.wait_for_function("[...document.querySelectorAll('figure svg.tall')].every(s=>s.getBoundingClientRect().width>200)")
        small = pg.evaluate("Math.min(...[...document.querySelectorAll('figure svg.tall text:not(.kt)')].filter(t=>t.textContent).map(t=>parseFloat(getComputedStyle(t).fontSize)*t.ownerSVGElement.getBoundingClientRect().width/t.ownerSVGElement.viewBox.baseVal.width))")
        ok(f"phone diagram text is readable ({small:.1f}px)", small >= 12)
        pg.route("**/*.glb", lambda r: r.abort())
        n_bad = len(bad)
        pg.set_viewport_size({"width": 1440, "height": 900})
        pg.goto(base + "boards/io2.html")
        pg.wait_for_function("document.querySelector('.mgo').textContent.includes('not available')||!document.querySelector('.mgo').disabled", timeout=20000)
        if not pg.locator("text=not available").count():
            pg.click(".mgo")
            pg.wait_for_selector("text=not available", timeout=20000)
        ok("failed 3D keeps the picture", pg.is_visible(".model img"))
        del bad[n_bad:]
        pg.unroute("**/*.glb")
        # no-JS and reduced motion
        c2 = p.chromium.launch(channel="msedge")
        q = c2.new_context(java_script_enabled=False).new_page()
        q.goto(base + "index.html")
        ok("readable without JS", "17.703169" in q.inner_text("#term"))
        c2.close()
        ctx.close()
    srv.shutdown()
    for b in dict.fromkeys(bad):
        print("FAIL", b)
    print(f"{len(pages)} pages x {len(SIZES)} sizes, {len(links)} links: " + ("PASS" if not bad else f"{len(set(bad))} problems"))
    return 1 if bad and a.check else 0


if __name__ == "__main__":
    sys.exit(main())
