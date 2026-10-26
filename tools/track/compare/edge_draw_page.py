#!/usr/bin/env python3
"""The owner's edge-drawing page: one canvas per outline window, with Line / Arc / Curve / Freehand / Select / Erase
tools, red strokes for the asphalt edge and green for an extra line (the end of a legitimate paved runoff). Written
for the Buttonwillow round-9 outline (23 Oct 2026, the owner: "As a human being I can't draw straight lines on my mac
touchpad") and kept for every later edge refit or track-builder escalation.

    uv run --python 3.12 python -I tools/track/compare/edge_draw_page.py --src <outline dir> --out <page dir> \
        --title "Buttonwillow Edge Strokes" [--coll edges] [--mpp 0.12]

--src is the outline page directory `build_track.py` writes for the owner checkpoint (`w_sNNNN.jpg` / `close_sNNNN.jpg`
windows plus an `index.html` whose <img src> / <figcaption> pairs give the captions; any directory of jpg/png windows
works, captions fall back to the file name). The page is written to <out>/edges.html with the windows copied to
<out>/win/; the orchestrator publishes it with the Artifact tool (`capabilities: {db: {}}`, files = `win/*`) and reads
the strokes back with ArtifactData (collection <coll>, one document per window id, `out_dir` to save them as JSON),
then renders them with `edge_draw_render.py`.

Stroke format (document fields): `w`, `h` (the window's image size), `margin` (the canvas margin in image pixels; the
owner may start a line there, so points may fall outside 0..w / 0..h), `strokes: [{c: 'red'|'green', kind: 'line'|
'arc'|'curve'|'free', ctrl: [[x, y]..], pts: [[x, y]..]}]` in image pixels (`ctrl` are the control points the Select
tool edits; `pts` is the sampled polyline to render; older strokes carry `pts` only).

Behaviour: every shape finishes on its last click (Line 2, Arc 3: start, end, a point on the arc; Curve: click the last
point again) and the next click starts a new one; Freehand drags; Select drags a point (joined ends move together) or the
whole stroke, Delete / Red / Green act on the selection; Erase removes the stroke under the tap; Undo / Clear per window;
Zoom 1-3x; the photo fits the viewport with no scroll bars at 1x. Every finished shape or edit saves on its own.
"""
import argparse
import html
import json
import os
import re
import shutil

CSS = '''<style>
:root{
  --bg:#eef0f2; --fg:#15181c; --muted:#5b6470; --card:#ffffff; --line:#d3d8de; --soft:#e3e7eb;
  --accent:#e8571c; --accent-ink:#ffffff; --ok:#2f8f5b; --ok-soft:#dff1e6; --warn:#b7791f;
  --display:"Barlow Condensed","Arial Narrow",Impact,sans-serif; --body:"Barlow","Helvetica Neue",Arial,sans-serif;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --bg:#14171b; --fg:#e9ecef; --muted:#9aa3ad; --card:#1d2126; --line:#30363d; --soft:#262b31;
  --accent:#ff6a2c; --accent-ink:#14171b; --ok:#5cc08a; --ok-soft:#1f3a2c; --warn:#d9a441; color-scheme:dark } }
:root[data-theme="dark"]{
  --bg:#14171b; --fg:#e9ecef; --muted:#9aa3ad; --card:#1d2126; --line:#30363d; --soft:#262b31;
  --accent:#ff6a2c; --accent-ink:#14171b; --ok:#5cc08a; --ok-soft:#1f3a2c; --warn:#d9a441; color-scheme:dark }
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 var(--body);padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:0 48px}
.wrap{max-width:720px;margin:0 auto}
header.top{position:sticky;top:0;z-index:9;background:var(--bg);padding-block:10px 6px;border-bottom:1px solid var(--line)}
header.top .row{display:flex;align-items:baseline;justify-content:space-between;gap:12px}
header.top h1{font:700 28px/1 var(--display);margin:0;letter-spacing:.01em}
header.top .count{font-size:13px;color:var(--muted);white-space:nowrap}
.bar{height:4px;background:var(--soft);border-radius:2px;margin-top:8px;overflow:hidden}.bar i{display:block;height:100%;width:0;background:var(--ok);transition:width .3s}
p.intro{font-size:15px;color:var(--muted);margin:14px 0 6px}
.banner{display:none;background:#fff3cd;color:#5c4400;border:1px solid #e5cf7a;border-radius:6px;padding:8px 12px;margin:8px 0;font-size:14px}.banner.show{display:block}
footer{font-size:13px;color:var(--muted);margin-top:24px}
.win{padding:18px 0 22px;border-top:1px solid var(--line)}
.win h3{font:700 22px/1.1 var(--display);margin:0 0 4px}
.win .cap{font-size:13.5px;color:var(--muted);margin:0 0 8px}
.tools{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:0 0 8px}
.tools button{font:600 14px/1 var(--body);padding:8px 12px;border-radius:999px;border:1.5px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
.tools button.on{border-color:var(--ok);background:var(--ok-soft)}
.tools button.red.on{border-color:#d0352a;background:#d0352a;color:#fff}
.tools button.green.on{border-color:#1f9a3f;background:#1f9a3f;color:#fff}
.tools button.delete{border-color:#d0352a;color:#d0352a}.tools button.delete:disabled{opacity:.4;cursor:default}
.tools button.tb{display:inline-flex;flex-direction:column;align-items:center;gap:4px;padding:6px 9px 5px;min-width:54px;font-size:11px;line-height:1;letter-spacing:.02em}
.tools button.tb svg{width:26px;height:22px;display:block;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.tools button.tb svg .dot{fill:currentColor;stroke:none}.tools button.tb svg .solid{fill:currentColor;stroke:none}
.tools button.sw{display:inline-flex;align-items:center;gap:7px}.tools button.sw i{display:inline-block;width:14px;height:14px;border-radius:50%;background:#d0352a}.tools button.sw.green i{background:#1f9a3f}
.tools button.sw.on i{background:#fff}
.tools .sep{width:1px;height:22px;background:var(--line);margin:0 4px}.tools .hint{font-size:12.5px;color:var(--muted);width:100%}.tools .st{font-size:13px;color:var(--muted);margin-left:auto;font-variant-numeric:tabular-nums}
.frame{overflow:hidden;border:1px solid var(--line);border-radius:4px;background:#2b2b2b;-webkit-overflow-scrolling:touch}
.frame.zoomed{overflow:auto}
.stage{position:relative;transform-origin:0 0;background:#2b2b2b}
.stage img{display:block;position:absolute;max-width:none;user-select:none;-webkit-user-drag:none;outline:1px solid #555}
.stage canvas{position:absolute;left:0;top:0;touch-action:auto}
.stage.draw canvas{touch-action:none;cursor:crosshair}
.stage.sel canvas{cursor:default}
</style>'''

ICON = {
    'line': '<svg viewBox="0 0 26 22"><line x1="4" y1="18" x2="22" y2="4"/><circle class="dot" cx="4" cy="18" r="2.4"/><circle class="dot" cx="22" cy="4" r="2.4"/></svg>',
    'arc': '<svg viewBox="0 0 26 22"><path d="M3 18 Q 13 -4 23 18"/><circle class="dot" cx="3" cy="18" r="2.4"/><circle class="dot" cx="23" cy="18" r="2.4"/><circle class="dot" cx="13" cy="7" r="2.4"/></svg>',
    'curve': '<svg viewBox="0 0 26 22"><path d="M2 16 C 6 2, 10 2, 13 11 S 20 20, 24 6"/><circle class="dot" cx="2" cy="16" r="2.2"/><circle class="dot" cx="13" cy="11" r="2.2"/><circle class="dot" cx="24" cy="6" r="2.2"/></svg>',
    'free': '<svg viewBox="0 0 26 22"><path d="M2 14 c 2 -8 4 -8 6 0 s 4 8 6 0 s 4 -8 6 0 s 2 4 4 2"/></svg>',
    'select': '<svg viewBox="0 0 26 22"><path class="solid" d="M4 2 l 12 10 -5 1 3.5 6 -2.5 1.2 -3.5 -6 -4.5 4 z"/><circle cx="21" cy="17" r="3"/></svg>',
    'erase': '<svg viewBox="0 0 26 22"><path d="M3 15 L 13 5 a 1.5 1.5 0 0 1 2 0 l 7 7 a 1.5 1.5 0 0 1 0 2 L 17 19 H 9 z"/><line x1="9" y1="19" x2="3" y2="15"/><line x1="8" y1="10" x2="17" y2="19"/></svg>',
}
TOOLS = ''.join(f'<button class="tool tb{" on" if t == "line" else ""}" data-tool="{t}" title="{lbl}">{ICON[t]}<span>{lbl}</span></button>'
                for t, lbl in [('line', 'Line'), ('arc', 'Arc'), ('curve', 'Curve'), ('free', 'Freehand'), ('select', 'Select'), ('erase', 'Erase')])

SCRIPT = r'''<script>
(function(){
  var COLL=%COLL%, state={}, db=null, chains={};
  var banner=document.getElementById('banner');
  function showBanner(m){ banner.textContent=m; banner.classList.add('show'); }
  var secs=Array.prototype.slice.call(document.querySelectorAll('section.win'));
  var KEYS=secs.map(function(s){ return s.dataset.key; });
  var W={};
  function strokes(k){ return (state[k]&&state[k].strokes)||[]; }
  function ctrlOf(st){ if(st.ctrl) return st.ctrl; if(st.kind==='free') return null; if(st.pts && st.pts.length<=12) return st.pts; return null; }
  function render(k){
    var w=W[k]; if(!w||!w.ready) return;
    var ctx=w.ctx, M=w.M; ctx.clearRect(0,0,w.canvas.width,w.canvas.height);
    ctx.save(); ctx.translate(M,M);
    var s=strokes(k); if(w.live) s=s.concat([w.live]);
    function path(st){ ctx.beginPath(); ctx.moveTo(st.pts[0][0],st.pts[0][1]); for(var i=1;i<st.pts.length;i++) ctx.lineTo(st.pts[i][0],st.pts[i][1]); if(st.pts.length===1) ctx.lineTo(st.pts[0][0]+0.1,st.pts[0][1]); }
    s.forEach(function(st,i){ if(!st.pts||st.pts.length<1) return; ctx.lineCap='round'; ctx.lineJoin='round';
      if(i===w.sel){ ctx.strokeStyle='rgba(255,255,255,0.9)'; ctx.lineWidth=10; path(st); ctx.stroke(); }
      ctx.strokeStyle=st.c==='green'?'#00e000':'#ff0000'; ctx.lineWidth=4; path(st); ctx.stroke(); });
    if(w.sel>=0 && s[w.sel]){ var C=ctrlOf(s[w.sel]); if(C){ var r=7/w.scale; C.forEach(function(p){ ctx.beginPath(); ctx.arc(p[0],p[1],r,0,2*Math.PI); ctx.fillStyle='#fff'; ctx.fill(); ctx.lineWidth=2/w.scale; ctx.strokeStyle=s[w.sel].c==='green'?'#1f9a3f':'#d0352a'; ctx.stroke(); }); } }
    ctx.restore();
    var n=strokes(k).length; w.st.textContent=n? n+' stroke'+(n>1?'s':'')+(w.saving?' · saving…':' · saved') : 'No strokes';
    if(w.bDelete) w.bDelete.disabled = !(w.sel>=0 && w.sel<n);
  }
  function progress(){ var n=KEYS.filter(function(k){ return strokes(k).length; }).length; document.getElementById('count').textContent=n+' of '+KEYS.length+' marked'; document.getElementById('barfill').style.width=Math.round(100*n/KEYS.length)+'%'; }
  function save(k){
    if(!db){ showBanner('Saving is not available in this view; strokes will be lost. Reply in chat instead.'); return; }
    var w=W[k]; w.saving=true; render(k);
    var body={strokes:strokes(k), w:w.imgW, h:w.imgH, margin:w.M, at:new Date().toISOString()};
    chains[k]=(chains[k]||Promise.resolve()).then(function(){ return db.doc(COLL+'/'+k).set(body); }).then(function(){ w.saving=false; render(k); }).catch(function(e){ w.saving=false; showBanner('Save failed on '+k+' ('+((e&&e.code)||'unavailable')+'); try the stroke again.'); render(k); });
  }
  secs.forEach(function(sec){
    var k=sec.dataset.key, img=sec.querySelector('img'), canvas=sec.querySelector('canvas'), stage=sec.querySelector('.stage'), frame=sec.querySelector('.frame');
    var w=W[k]={canvas:canvas, ctx:canvas.getContext('2d'), st:sec.querySelector('.st'), color:'red', zoom:1, draw:false, live:null, ready:false, sel:-1, M:0, imgW:0, imgH:0};
    function fit(){
      var iw=img.naturalWidth, ih=img.naturalHeight; var M=Math.round(0.1*Math.max(iw,ih)); w.M=M; w.imgW=iw; w.imgH=ih;
      var sw=iw+2*M, sh=ih+2*M;
      img.style.left=M+'px'; img.style.top=M+'px';
      canvas.width=sw; canvas.height=sh; canvas.style.width=sw+'px'; canvas.style.height=sh+'px';
      stage.style.width=sw+'px'; stage.style.height=sh+'px';
      var maxH=Math.max(300, window.innerHeight*0.84);
      var base=Math.min(frame.clientWidth/sw, maxH/sh); var scale=base*w.zoom;
      stage.style.transform='scale('+scale+')';
      frame.classList.toggle('zoomed', w.zoom>1);
      frame.style.height=(w.zoom>1 ? Math.min(sh*scale, maxH) : sh*scale)+2+'px';
      w.scale=scale; w.ready=true; render(k); }
    if(img.complete && img.naturalWidth) fit(); else img.addEventListener('load', fit);
    window.addEventListener('resize', function(){ if(img.naturalWidth) fit(); });
    var bDraw=sec.querySelector('.draw'), bRed=sec.querySelector('.red'), bGreen=sec.querySelector('.green'), bZoom=sec.querySelector('.zoom'), bDelete=sec.querySelector('.delete'); w.bDelete=bDelete;
    bDraw.addEventListener('click', function(){ w.draw=!w.draw; bDraw.classList.toggle('on', w.draw); stage.classList.toggle('draw', w.draw); bDraw.textContent=w.draw?'Drawing':'Draw'; if(!w.draw){ cancelShape(); } });
    function recolour(c){ w.color=c; bRed.classList.toggle('on', c==='red'); bGreen.classList.toggle('on', c==='green');
      if(w.tool==='select' && w.sel>=0 && strokes(k)[w.sel]){ var s=strokes(k).slice(); s[w.sel]=Object.assign({}, s[w.sel], {c:c}); state[k]={strokes:s}; render(k); save(k); } }
    bRed.addEventListener('click', function(){ recolour('red'); });
    bGreen.addEventListener('click', function(){ recolour('green'); });
    bZoom.addEventListener('click', function(){ w.zoom = w.zoom>=3 ? 1 : w.zoom+1; bZoom.textContent='Zoom '+w.zoom+'x'; fit(); });
    sec.querySelector('.undo').addEventListener('click', function(){ var s=strokes(k); if(!s.length) return; state[k]={strokes:s.slice(0,-1)}; if(w.sel>=s.length-1) w.sel=-1; render(k); progress(); save(k); });
    sec.querySelector('.clear').addEventListener('click', function(){ if(!strokes(k).length) return; state[k]={strokes:[]}; w.sel=-1; render(k); progress(); save(k); });
    function deleteSel(){ var s=strokes(k); if(!(w.sel>=0 && w.sel<s.length)) return; s=s.slice(); s.splice(w.sel,1); state[k]={strokes:s}; w.sel=-1; render(k); progress(); save(k); setHint(); }
    bDelete.addEventListener('click', deleteSel);
    function pos(ev){ var r=canvas.getBoundingClientRect(); return [Math.round(((ev.clientX-r.left)/w.scale-w.M)*10)/10, Math.round(((ev.clientY-r.top)/w.scale-w.M)*10)/10]; }
    w.tool='line'; w.pending=[]; w.hover=null; w.drag=null;
    var hint=document.createElement('span'); hint.className='hint'; sec.querySelector('.tools').appendChild(hint);
    function setHint(){ var m={line:'Line: click the start, then the end.', arc:'Arc: click the start, the end, then a point the arc passes through.', curve:'Curve: click points along the edge; click the last point again to finish.', free:'Freehand: drag to draw.', select: (w.sel>=0 ? 'Line selected: drag a point to move it, drag the line to move it whole, Delete removes it, Red/Green recolours it.' : 'Select: tap a line to pick it.'), erase:'Erase: tap a line to remove it.'}; hint.textContent=(w.pending.length? w.pending.length+' point'+(w.pending.length>1?'s':'')+' placed. ':'')+m[w.tool]; }
    setHint();
    sec.querySelectorAll('.tool').forEach(function(b){ b.addEventListener('click', function(){ cancelShape(); w.tool=b.dataset.tool; if(w.tool!=='select'){ w.sel=-1; } stage.classList.toggle('sel', w.tool==='select'||w.tool==='erase'); sec.querySelectorAll('.tool').forEach(function(x){ x.classList.toggle('on', x===b); }); render(k); setHint(); }); });
    function commit(st){ if(!st||!st.pts||st.pts.length<2) return; var s=strokes(k).concat([st]); state[k]={strokes:s}; render(k); progress(); save(k); }
    function arcPts(a,b,c){ // circle through a, c, b; sample from a to b through c
      var ax=a[0],ay=a[1],bx=b[0],by=b[1],cx=c[0],cy=c[1];
      var d=2*(ax*(cy-by)+cx*(by-ay)+bx*(ay-cy)); if(Math.abs(d)<1e-6) return [a,b];
      var ux=((ax*ax+ay*ay)*(cy-by)+(cx*cx+cy*cy)*(by-ay)+(bx*bx+by*by)*(ay-cy))/d;
      var uy=((ax*ax+ay*ay)*(bx-cx)+(cx*cx+cy*cy)*(ax-bx)+(bx*bx+by*by)*(cx-ax))/d;
      var r=Math.hypot(ax-ux,ay-uy), ta=Math.atan2(ay-uy,ax-ux), tb=Math.atan2(by-uy,bx-ux), tc=Math.atan2(cy-uy,cx-ux);
      function norm(x){ while(x<0) x+=2*Math.PI; return x%(2*Math.PI); }
      var ccwB=norm(tb-ta), ccwC=norm(tc-ta); var sweep = ccwC<ccwB ? ccwB : ccwB-2*Math.PI; // go the way that passes c
      var n=Math.max(8, Math.min(400, Math.round(Math.abs(sweep)*r/4))); var out=[];
      for(var i=0;i<=n;i++){ var th=ta+sweep*i/n; out.push([Math.round((ux+r*Math.cos(th))*10)/10, Math.round((uy+r*Math.sin(th))*10)/10]); }
      return out; }
    function splinePts(P){ if(P.length<3) return P.slice(); var out=[]; for(var i=0;i<P.length-1;i++){ var p0=P[Math.max(0,i-1)],p1=P[i],p2=P[i+1],p3=P[Math.min(P.length-1,i+2)]; var seg=Math.hypot(p2[0]-p1[0],p2[1]-p1[1]); var n=Math.max(4,Math.min(200,Math.round(seg/4))); for(var j=0;j<n;j++){ var s=j/n,s2=s*s,s3=s2*s; out.push([Math.round((0.5*((2*p1[0])+(-p0[0]+p2[0])*s+(2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*s2+(-p0[0]+3*p1[0]-3*p2[0]+p3[0])*s3))*10)/10, Math.round((0.5*((2*p1[1])+(-p0[1]+p2[1])*s+(2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*s2+(-p0[1]+3*p1[1]-3*p2[1]+p3[1])*s3))*10)/10]); } } out.push(P[P.length-1]); return out; }
    function regen(st){ var C=st.ctrl; if(!C) return st; var kind=st.kind||'line';
      if(kind==='arc' && C.length===3) st.pts=arcPts(C[0],C[1],C[2]); else if(kind==='curve') st.pts=splinePts(C); else st.pts=C.map(function(p){ return p.slice(); }); return st; }
    function mk(kind, ctrl, pts){ return {c:w.color, kind:kind, ctrl:ctrl, pts:pts}; }
    function preview(){ var P=w.pending, h=w.hover; w.live=null;
      if(w.tool==='line'){ if(P.length){ w.live={c:w.color, pts: h? P.concat([h]) : P.slice()}; } }
      else if(w.tool==='arc'){ if(P.length===1){ w.live={c:w.color, pts: h? [P[0],h] : [P[0]]}; } else if(P.length===2){ w.live={c:w.color, pts: h? arcPts(P[0],P[1],h) : [P[0],P[1]]}; } }
      else if(w.tool==='curve'){ if(P.length){ w.live={c:w.color, pts: splinePts(h? P.concat([h]) : P)}; } }
      render(k); }
    function finishShape(){ var P=w.pending; if(w.tool==='curve'&&P.length>=2) commit(mk('curve', P.slice(), splinePts(P))); w.pending=[]; w.hover=null; w.live=null; render(k); setHint(); }
    function cancelShape(){ w.pending=[]; w.hover=null; w.live=null; w.drag=null; render(k); setHint(); }
    function near(a,b){ return Math.hypot(a[0]-b[0],a[1]-b[1])<3/w.scale; }
    function onLast(p){ var P=w.pending; return P.length>=2 && Math.hypot(p[0]-P[P.length-1][0], p[1]-P[P.length-1][1])<12/w.scale; }
    function segDist(p,a,b){ var dx=b[0]-a[0], dy=b[1]-a[1], L=dx*dx+dy*dy; var t = L? Math.max(0, Math.min(1, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L)) : 0; return Math.hypot(p[0]-(a[0]+t*dx), p[1]-(a[1]+t*dy)); }
    function hitStroke(p){ var s=strokes(k), best=-1, bd=9/w.scale; s.forEach(function(st,i){ if(!st.pts||st.pts.length<1) return; for(var j=0;j<Math.max(1,st.pts.length-1);j++){ var d=segDist(p, st.pts[j], st.pts[Math.min(j+1,st.pts.length-1)]); if(d<bd){ bd=d; best=i; } } }); return best; }
    function hitHandle(p){ var s=strokes(k); if(!(w.sel>=0 && s[w.sel])) return -1; var C=ctrlOf(s[w.sel]); if(!C) return -1; var best=-1, bd=12/w.scale; C.forEach(function(q,i){ var d=Math.hypot(p[0]-q[0],p[1]-q[1]); if(d<bd){ bd=d; best=i; } }); return best; }
    function editable(st){ var C=ctrlOf(st); if(!C) return st; var o=Object.assign({}, st); o.kind=st.kind||'line'; o.ctrl=C.map(function(p){ return p.slice(); }); return o; }
    function startDrag(p){ var s=strokes(k).slice(); var hi=hitHandle(p);
      if(hi>=0){ var st=editable(s[w.sel]); s[w.sel]=st; var origin=st.ctrl[hi].slice(); var joined=[]; // other strokes' control points sitting on this one move with it
        s.forEach(function(o,i){ if(i===w.sel) return; var C=ctrlOf(o); if(!C) return; C.forEach(function(q,j){ if(Math.hypot(q[0]-origin[0],q[1]-origin[1])<1.5){ var e=editable(o); s[i]=e; joined.push([i,j]); } }); });
        state[k]={strokes:s}; w.drag={mode:'handle', i:hi, joined:joined, moved:false}; return; }
      var si=hitStroke(p); if(si<0){ w.sel=-1; render(k); setHint(); return; }
      w.sel=si; var e=editable(s[si]); s[si]=e; state[k]={strokes:s}; w.drag={mode:'move', last:p, moved:false}; render(k); setHint(); }
    function moveDrag(p){ var d=w.drag; if(!d) return; var s=strokes(k).slice(); var st=s[w.sel]; if(!st) return;
      if(d.mode==='handle'){ st=Object.assign({}, st); st.ctrl=st.ctrl.map(function(q){ return q.slice(); }); st.ctrl[d.i]=p; regen(st); s[w.sel]=st;
        d.joined.forEach(function(ij){ var o=Object.assign({}, s[ij[0]]); o.ctrl=o.ctrl.map(function(q){ return q.slice(); }); o.ctrl[ij[1]]=p; regen(o); s[ij[0]]=o; }); }
      else { var dx=p[0]-d.last[0], dy=p[1]-d.last[1]; d.last=p; st=Object.assign({}, st); var sh=function(q){ return [Math.round((q[0]+dx)*10)/10, Math.round((q[1]+dy)*10)/10]; };
        if(st.ctrl){ st.ctrl=st.ctrl.map(sh); regen(st); } else { st.pts=st.pts.map(sh); } s[w.sel]=st; }
      d.moved=true; state[k]={strokes:s}; render(k); }
    function endDrag(){ var d=w.drag; w.drag=null; if(d && d.moved) save(k); }
    canvas.addEventListener('pointerdown', function(ev){ if(!w.draw) return; ev.preventDefault(); var p=pos(ev);
      if(w.tool==='select'){ canvas.setPointerCapture(ev.pointerId); startDrag(p); return; }
      if(w.tool==='erase'){ var ei=hitStroke(p); if(ei>=0){ var es=strokes(k).slice(); es.splice(ei,1); state[k]={strokes:es}; w.sel=-1; render(k); progress(); save(k); } return; }
      if(w.tool==='free'){ canvas.setPointerCapture(ev.pointerId); w.freeLive={c:w.color, pts:[p]}; w.live=w.freeLive; render(k); return; }
      var P=w.pending;
      if(w.tool==='curve' && onLast(p)){ finishShape(); return; }
      if(P.length && near(p,P[P.length-1])) return;
      if(w.tool==='line'){ P.push(p); if(P.length>=2){ commit(mk('line', [P[0],P[1]], [P[0],P[1]])); w.pending=[]; w.hover=null; w.live=null; render(k); setHint(); return; } }
      else if(w.tool==='arc'){ P.push(p); if(P.length===3){ commit(mk('arc', [P[0],P[1],P[2]], arcPts(P[0],P[1],P[2]))); w.pending=[]; w.hover=null; w.live=null; render(k); setHint(); return; } }
      else if(w.tool==='curve'){ P.push(p); }
      w.hover=p; preview(); setHint(); });
    canvas.addEventListener('pointermove', function(ev){ if(!w.draw) return; var p=pos(ev);
      if(w.tool==='select'){ if(w.drag){ ev.preventDefault(); moveDrag(p); } return; }
      if(w.tool==='erase') return;
      if(w.tool==='free'){ if(!w.freeLive) return; ev.preventDefault(); var last=w.freeLive.pts[w.freeLive.pts.length-1]; if(Math.abs(p[0]-last[0])+Math.abs(p[1]-last[1])<1.5) return; w.freeLive.pts.push(p); render(k); return; }
      if(w.pending.length){ w.hover=p; preview(); } });
    function endFree(ev){ if(!w.draw) return; if(w.tool==='select'){ endDrag(); return; } if(w.tool==='erase') return; if(!w.freeLive) return; ev.preventDefault(); var st=w.freeLive; w.freeLive=null; w.live=null; if(st.pts.length>=2) commit({c:w.color, kind:'free', pts:st.pts}); else render(k); }
    canvas.addEventListener('pointerup', endFree); canvas.addEventListener('pointercancel', endFree);
    canvas.addEventListener('dblclick', function(ev){ ev.preventDefault(); });
    sec.addEventListener('keydown', function(ev){ if(ev.key==='Escape'){ cancelShape(); } else if(ev.key==='Enter'){ finishShape(); } else if((ev.key==='Delete'||ev.key==='Backspace') && w.tool==='select' && w.sel>=0){ ev.preventDefault(); deleteSel(); } });
    canvas.setAttribute('tabindex','0'); canvas.addEventListener('pointerdown', function(){ try{ canvas.focus({preventScroll:true}); }catch(e){} });
  });
  progress();
  var use=(window.claude && typeof window.claude.use==='function') ? window.claude.use.bind(window.claude) : function(){ return Promise.resolve(null); };
  use('db').then(function(d){
    db=d; if(!db){ showBanner('Saving is not available in this view, so strokes will not be kept.'); return; }
    db.collection(COLL).onSnapshot(function(snap){ var next={}; snap.docs.forEach(function(doc){ if(doc.exists){ var x=doc.data()||{}; next[doc.id]={strokes:x.strokes||[]}; } }); KEYS.forEach(function(k){ if(W[k]&&(W[k].saving||W[k].drag)) { next[k]=state[k]; } }); state=next; KEYS.forEach(function(k){ if(W[k] && W[k].sel>=strokes(k).length) W[k].sel=-1; render(k); }); progress(); }, function(e){ showBanner('Live updates stopped ('+((e&&e.code)||'unavailable')+'). Strokes still save; reload to see them.'); });
  }).catch(function(){ showBanner('Saving is not available in this view.'); });
})();
</script>
'''


def window_key(name):
    """Sort key: full windows (w_) before close-ups, then by station."""
    m = re.search(r's(\d+)', name)
    return (0 if name.startswith('w_') else 1, int(m.group(1)) if m else 0, name)


def read_captions(src):
    page = os.path.join(src, 'index.html')
    caps = {}
    if os.path.exists(page):
        text = open(page, encoding='utf-8').read()
        for img, cap in re.findall(r'<img[^>]+src="([^"]+\.(?:jpe?g|png))"[^>]*>.*?<figcaption>(.*?)</figcaption>', text, re.S | re.I):
            cap = html.unescape(re.sub(r'<[^>]+>', ' ', cap))
            caps[os.path.basename(img)] = re.sub(r'\s+', ' ', cap).strip()
    return caps


def build(src, out, title, coll='edges', intro=None):
    os.makedirs(os.path.join(out, 'win'), exist_ok=True)
    caps = read_captions(src)
    wins = sorted((f for f in os.listdir(src) if f.lower().endswith(('.jpg', '.jpeg', '.png'))), key=window_key)
    items = []
    for f in wins:
        shutil.copy(os.path.join(src, f), os.path.join(out, 'win', f))
        items.append({'id': os.path.splitext(f)[0], 'file': 'win/' + f, 'cap': caps.get(f, os.path.splitext(f)[0])})
    n = len(items)
    E = html.escape
    intro = intro or (f'The drawn edges over the captures, {n} windows round the lap. Where the drawn edge is off the asphalt, tap '
                      '<b>Draw</b> on that window and mark the correct asphalt edge in <b>red</b>; use <b>green</b> only for an extra line, '
                      'such as the end of a legitimate paved runoff. The dark margin round each photo is part of the canvas, so a line can '
                      'start or end there. Each shape finishes on its last click, and the next click starts a new one. <b>Line</b>: click the '
                      'start, then the end. <b>Arc</b>: click the start, the end, then a point the arc should pass through. <b>Curve</b>: click '
                      'points along the edge, then click the last point again to finish; a smooth curve runs through them. <b>Freehand</b> draws '
                      'as you drag. <b>Select</b>: tap a line to pick it; drag one of its points to move that point (joined ends move together), '
                      'drag the line itself to move the whole thing; <b>Delete</b> removes it and Red/Green recolours it. <b>Erase</b>: tap a line '
                      'to remove it. Escape drops the shape in progress. Every finished shape or edit saves on its own. Skip windows that look '
                      'right; zoom for precision; with Draw off, the page scrolls normally.')
    head = (f'<title>{E(title)}</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Barlow:wght@400;500;600&display=swap">\n'
            + CSS + '\n')
    parts = [f'''<div class="wrap">
<header class="top">
  <div class="row"><h1>{E(title)}</h1><span class="count" id="count">0 of {n} marked</span></div>
  <div class="bar"><i id="barfill"></i></div>
</header>
<p class="intro">{intro}</p>
<div class="banner" id="banner"></div>
''']
    for i, it in enumerate(items, 1):
        k = it['id']
        label = k.replace('w_s', 'station ').replace('close_s', 'close-up at ')
        parts.append(f'''<section class="win" id="{E(k)}" data-key="{E(k)}">
  <h3>{i} of {n}: {E(label)}</h3>
  <p class="cap">{E(it['cap'])}</p>
  <div class="tools">
    <button class="draw">Draw</button><span class="sep"></span>
    {TOOLS}<span class="sep"></span>
    <button class="red sw on"><i></i>Red</button><button class="green sw"><i></i>Green</button><span class="sep"></span>
    <button class="delete" disabled>Delete</button><button class="undo">Undo</button><button class="clear">Clear</button><button class="zoom">Zoom 1x</button>
    <span class="st" aria-live="polite">No strokes</span>
  </div>
  <div class="frame"><div class="stage"><img src="{it['file']}" alt="Outline window {E(k)}" loading="lazy"><canvas></canvas></div></div>
</section>
''')
    parts.append("<footer>Strokes save to this page's own store in image pixels; they are rendered onto the capture windows and read by the edge digitiser.</footer>\n</div>\n")
    parts.append(SCRIPT.replace('%COLL%', json.dumps(coll)))
    page = os.path.join(out, 'edges.html')
    open(page, 'w', encoding='utf-8').write(head + ''.join(parts))
    files = [{'path': it['file']} for it in items]
    json.dump({'coll': coll, 'files': files, 'windows': [it['id'] for it in items]}, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    return page, items


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--src', required=True, help='outline page directory (windows + index.html with figcaptions)')
    ap.add_argument('--out', required=True, help='page directory to write (edges.html, win/, manifest.json)')
    ap.add_argument('--title', required=True)
    ap.add_argument('--coll', default='edges', help='artifact db collection name (default edges)')
    ap.add_argument('--intro', help='intro paragraph (HTML) in place of the whole-lap default (a later local refit: the changed region only)')
    a = ap.parse_args()
    page, items = build(a.src, a.out, a.title, a.coll, a.intro)
    print(f'{len(items)} windows -> {page} ({os.path.getsize(page)} bytes); publish with capabilities {{db: {{}}}} and files win/*')


if __name__ == '__main__':
    main()
