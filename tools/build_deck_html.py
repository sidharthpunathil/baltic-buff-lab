"""Bundle a Slides-type deck folder (deck.json, deck.css, slides/*.html) into one self-contained HTML
slideshow with Prev/Next, keyboard, swipe, progress bar and speaker notes ('n').
Usage: python3 -I tools/build_deck_html.py deck/src/<name> deck/<out>.html"""
import json, re, sys, pathlib

src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
idx = json.loads((src / "deck.json").read_text())
css = (src / "deck.css").read_text(encoding="utf-8")
slides = []
for sid in idx["order"]:
    s = (src / "slides" / f"{sid}.html").read_text(encoding="utf-8").strip()
    slides.append(re.sub(r"<aside>(.*?)</aside>", r'<aside class="notes">\1</aside>', s, flags=re.S))
font = next(iter(idx["faces"].values()))["href"]
page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{idx['title']}</title>
<link rel="stylesheet" href="{font}">
<style>
{css}
html,body{{margin:0;height:100%;background:#0B0C1C;overflow:hidden}}
/* same base the Slides renderer applies: no default margins, its own table hairlines */
#deck *{{margin:0}}
#deck p,#deck li,#deck h1,#deck h2,#deck h3,#deck td,#deck th{{overflow-wrap:break-word}}
#deck table{{border-collapse:collapse}}
#deck th,#deck td{{padding:.35em .6em;text-align:left;vertical-align:top;border-bottom:1px solid rgba(140,144,170,.35)}}
#deck th{{font-weight:600;border-bottom:2px solid rgba(140,144,170,.6)}}
#stage{{position:fixed;left:0;right:0;top:0;bottom:var(--navh);overflow-x:hidden;overflow-y:auto;overscroll-behavior:contain}}
#spacer{{width:1px}}
:root{{--navh:72px}}
#deck{{width:1920px;height:1080px;position:absolute;left:0;top:0;transform-origin:0 0;border-radius:6px;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,.45)}}
#deck>section{{position:absolute;inset:0;box-sizing:border-box;display:none}}
#deck>section.active{{display:flex}}
#deck>section .in{{animation:none}}
#deck>section.active .in{{animation:rise 600ms cubic-bezier(0.16,1,0.3,1) both;animation-delay:calc(var(--i,0)*110ms)}}
x-shape{{display:block}} x-shape[kind="arrow-right"]{{clip-path:polygon(0 30%,60% 30%,60% 0,100% 50%,60% 100%,60% 70%,0 70%)}}
aside.notes{{display:none}}
body.shownotes aside.notes{{display:block;position:absolute;left:128px;right:128px;bottom:24px;font-size:22px;line-height:1.4;background:rgba(10,11,24,.92);color:#F4F5EE;padding:16px 20px;border-radius:12px}}
#nav{{position:fixed;left:0;right:0;bottom:0;height:var(--navh);display:flex;gap:10px;align-items:center;justify-content:center;font:600 15px system-ui,sans-serif;color:#F4F5EE;z-index:9;background:#0B0C1C;border-top:1px solid #23264A}}
#nav button{{background:#1C1E40;color:#F4F5EE;border:1px solid #34375E;border-radius:999px;padding:10px 18px;font:inherit;cursor:pointer;min-width:44px;min-height:44px}}
#nav button:hover{{background:#3A30F0}} #nav button:focus-visible{{outline:2px solid #D4FF00;outline-offset:2px}}
#count{{padding:0 8px;font-variant-numeric:tabular-nums}}
#bar{{position:fixed;top:0;left:0;height:4px;background:#D4FF00;z-index:9;transition:width .3s}}
/* Read mode: reflow slides into one column for phones */
body.read #deck{{position:static;transform:none!important;width:auto;height:auto;border-radius:0;box-shadow:none;overflow:visible}}
body.read #spacer{{display:none}}
body.read #deck>section{{display:flex!important;position:relative;inset:auto;height:auto;min-height:0;padding:28px 18px 32px;gap:16px;border-bottom:1px solid #2A2D4A}}
body.read #deck .row{{flex-direction:column;gap:12px;align-items:stretch!important}}
body.read #deck [style*="grid-template-columns"]{{grid-template-columns:1fr!important;grid-template-rows:auto!important}}
body.read #deck .fill{{flex:none}}
body.read #deck x-shape{{display:none}}
body.read #deck p,body.read #deck li,body.read #deck td,body.read #deck th,body.read #deck .body,body.read #deck .small,body.read #deck .lede{{font-size:16px!important;line-height:1.45!important}}
body.read #deck .eyebrow,body.read #deck .tag,body.read #deck .meta,body.read #deck .path,body.read #deck .barlabel{{font-size:12px!important;letter-spacing:.5px}}
body.read #deck h1{{font-size:40px!important}} body.read #deck h2{{font-size:26px!important;line-height:1.2}} body.read #deck h3{{font-size:19px!important}}
body.read #deck .big{{font-size:64px!important}} body.read #deck .quote{{font-size:24px!important;padding-left:14px;border-left-width:4px}}
body.read #deck .code{{font-size:13px!important;padding:14px;overflow-x:auto}}
body.read #deck .card,body.read #deck .stage{{padding:16px!important;border-radius:14px}}
body.read #deck table{{display:block;overflow-x:auto;width:100%}}
body.read #deck th,body.read #deck td{{width:auto!important;min-width:90px}}
body.read #deck [style*="width:"]:not(table):not(th):not(td){{max-width:100%}}
body.read #deck .in{{animation:none!important}}
body.read aside.notes{{display:block!important;position:static;font-size:14px;background:#191C33;color:#B7BAD4;padding:10px 12px;border-radius:10px}}
@media (prefers-reduced-motion:reduce){{#deck>section.active .in{{animation:none}}#bar{{transition:none}}}}
</style></head><body>
<div id="bar"></div>
<div id="stage"><div id="spacer"></div><div id="deck" role="region" aria-roledescription="slideshow" aria-label="{idx['title']}">
{chr(10).join(slides)}
</div></div>
<nav id="nav" aria-label="Slide navigation"><button id="prev" aria-label="Previous slide">← Prev</button><span id="count" aria-live="polite"></span><button id="next" aria-label="Next slide">Next →</button><button id="fitbtn" aria-label="Toggle fit mode">Fit width</button><button id="notes" aria-pressed="false" aria-label="Toggle speaker notes">Notes</button></nav>
<script>
const s=[...document.querySelectorAll('#deck>section')];let i=0;const deck=document.getElementById('deck');
let mode='auto';const MODES=['screen','width','read'];function fit(){{const st=document.getElementById('stage');const pad=16;const W=st.clientWidth-2*pad,H=st.clientHeight-2*pad;const kH=Math.min(W/1920,H/1080),kW=Math.min(W/1920,1.25);let m=mode;if(m==='auto')m=W<760?'read':(kH<0.6&&kW>kH*1.2?'width':'screen');document.body.classList.toggle('read',m==='read');document.body.dataset.fit=m;const label={{screen:'Fit width',width:'Read',read:'Fit screen'}};document.getElementById('fitbtn').textContent=label[m];if(m==='read'){{deck.style.transform='';deck.style.left='';deck.style.top='';return;}}const k=Math.max(0.05,m==='width'?kW:kH);deck.style.transform='scale('+k+')';deck.style.left=(st.clientWidth-1920*k)/2+'px';deck.style.top=(m==='width'?pad:Math.max(pad,(st.clientHeight-1080*k)/2))+'px';document.getElementById('spacer').style.height=(m==='width'?1080*k+2*pad:0)+'px';}}
function go(n){{i=Math.max(0,Math.min(s.length-1,n));s.forEach((e,j)=>{{e.classList.toggle('active',j===i);e.setAttribute('aria-hidden',document.body.dataset.fit!=='read'&&j!==i)}});
document.getElementById('count').textContent=(i+1)+' / '+s.length;document.getElementById('bar').style.width=((i+1)/s.length*100)+'%';
document.getElementById('prev').disabled=i===0;document.getElementById('next').disabled=i===s.length-1;history.replaceState(null,'','#'+(i+1));if(document.body.dataset.fit==='read'){{s[i].scrollIntoView({{block:'start'}});}}else{{document.getElementById('stage').scrollTop=0;}}}}
function notes(){{const on=document.body.classList.toggle('shownotes');document.getElementById('notes').setAttribute('aria-pressed',on);}}
document.getElementById('prev').onclick=()=>go(i-1);document.getElementById('next').onclick=()=>go(i+1);document.getElementById('notes').onclick=notes;document.getElementById('fitbtn').onclick=()=>{{const c=document.body.dataset.fit;mode=MODES[(MODES.indexOf(c)+1)%3];fit();go(i);}};
addEventListener('keydown',e=>{{if(['ArrowRight','PageDown',' '].includes(e.key)){{e.preventDefault();go(i+1)}}if(['ArrowLeft','PageUp'].includes(e.key))go(i-1);if(e.key==='Home')go(0);if(e.key==='End')go(s.length-1);if(e.key==='n')notes();if(e.key==='f')document.getElementById('fitbtn').click();}});
let x0=null;addEventListener('touchstart',e=>x0=e.touches[0].clientX,{{passive:true}});addEventListener('touchend',e=>{{if(x0===null)return;const d=e.changedTouches[0].clientX-x0;if(Math.abs(d)>40)go(i+(d<0?1:-1));x0=null;}});
addEventListener('resize',fit);if(window.visualViewport)visualViewport.addEventListener('resize',fit);new ResizeObserver(fit).observe(document.getElementById('stage'));fit();go((parseInt(location.hash.slice(1))||1)-1);
</script></body></html>"""
out.write_text(page, encoding="utf-8")
print(out, len(slides), "slides", len(page) // 1024, "KB")
