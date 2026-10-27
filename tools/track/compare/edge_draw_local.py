#!/usr/bin/env python3
"""Build the existing edge drawing page for local review without an Artifact DB.

    python3 -I tools/track/compare/edge_draw_local.py --src <outline-dir> \
        --out <review-dir> --title 'Mid-Ohio edge review'

Serve the result over localhost. Marks persist in that browser, keyed to the
actual window images. Download marks before changing browser or server origin.
The downloaded JSON maps window IDs to the same per-window documents consumed
by edge_draw_render.py; split them into files there before rendering.
Reference images remain local and must never be committed or used as textures.

For browser-local carry-over, add --import-review <old-review-dir>
--source-windows <old-windows.json> --target-windows <new-windows.json>.
The old page and its storage remain unchanged. A read-only bridge attempts
carry-over on load. Bring original marks opens the source directly if embedded
storage is blocked; file import is also supported. Marks are mapped through ENU
coordinates and merged with existing edits. Ports default to 5197 and 5198.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re


ADAPTER = r'''<script>
(function () {
  'use strict';
  var key = %KEY%, records = {}, listeners = [], readError = '';
  try { records = JSON.parse(localStorage.getItem(key) || '{}'); }
  catch (e) { readError = 'Could not restore marks. Download any new marks before closing this page.'; }
  function notify() {
    var snap = {docs: Object.keys(records).map(function (id) {
      return {id: id, exists: true, data: function () { return records[id]; }};
    })};
    listeners.forEach(function (fn) { fn(snap); });
  }
  var db = {
    doc: function (path) { return {set: function (body) {
      var id = path.slice(path.indexOf('/') + 1);
      records[id] = body;
      try { localStorage.setItem(key, JSON.stringify(records)); }
      catch (e) { return Promise.reject(e); }
      // Let the drawing page finish its saving state before a snapshot refresh.
      setTimeout(notify, 0);
      return Promise.resolve();
    }}; },
    collection: function () { return {onSnapshot: function (fn) {
      listeners.push(fn); fn({docs: Object.keys(records).map(function (id) {
        return {id: id, exists: true, data: function () { return records[id]; }};
      })});
    }}; }
  };
  window.claude = {use: function () { return Promise.resolve(db); }};
%TRANSFER%
  document.addEventListener('DOMContentLoaded', function () {
    var intro = document.querySelector('.intro');
    var controls = document.createElement('p');
    var button = document.createElement('button');
    button.textContent = 'Download marks';
    button.style.cssText = 'padding:10px 16px;cursor:pointer';
    button.addEventListener('click', function () {
      var blob = new Blob([JSON.stringify(records, null, 2)], {type: 'application/json'});
      var url = URL.createObjectURL(blob), a = document.createElement('a');
      a.href = url; a.download = 'edge-marks.json'; a.click();
      setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    });
    controls.appendChild(button);
    controls.appendChild(document.createTextNode(' Marks save in this browser. Download them to send your corrections back.'));
    intro.insertAdjacentElement('afterend', controls);
    document.querySelector('footer').textContent = 'Marks are stored locally in this browser. Download marks to share them for the next fit.';
    if (readError) {
      var banner = document.getElementById('banner');
      banner.textContent = readError; banner.classList.add('show');
    }
  });
})();
</script>'''


TRANSFER = r'''
  document.addEventListener('DOMContentLoaded', function () {
    var config = %CONFIG%, frames = [], imported = 0, recognized = 0, popup = null;
    var panel = document.createElement('div'), status = document.createElement('span');
    panel.style.cssText = 'display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:8px 0;font-size:13px';
    var bring = document.createElement('button'); bring.textContent = 'Bring original marks'; bring.id = 'bring-original-marks';
    var load = document.createElement('button'); load.textContent = 'Load original marks file';
    [bring, load].forEach(function (button) { button.style.cssText = 'padding:8px 10px;cursor:pointer'; panel.appendChild(button); });
    var file = document.createElement('input'); file.type = 'file'; file.accept = '.json,application/json'; file.hidden = true;
    panel.appendChild(file); status.setAttribute('role', 'status'); status.id = 'mark-transfer-status'; panel.appendChild(status);
    document.querySelector('header.top').appendChild(panel);
    function showTransfer(message) { status.textContent = message; }
    showTransfer('Checking for original marks…');
    var ledgerKey = key + ':imports', ledger = [];
    try { ledger = JSON.parse(localStorage.getItem(ledgerKey) || '[]'); }
    catch (e) { showTransfer('Could not read transfer history; originals remain untouched.'); return; }
    function nonce() { return crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random(); }
    function importDocuments(documents, explicit) {
      var result = EdgeMarkTransfer.merge(records, documents || {}, explicit ? [] : ledger,
                                           config.sourceWindows, config.targetWindows, config.sourceKey);
      if (result.recognized) {
        localStorage.setItem(key, JSON.stringify(result.records));
        records = result.records; ledger = Array.from(new Set(ledger.concat(result.imports))); notify();
        imported += result.added; recognized += result.recognized;
        localStorage.setItem(ledgerKey, JSON.stringify(ledger));
      }
      if (imported) showTransfer('Carried over ' + imported + ' original mark' + (imported === 1 ? '' : 's') + '. Original and round-two edits are preserved.');
      else if (recognized) showTransfer('Previous transfer detected. Bring original marks restores any missing marks; round-two edits are preserved.');
      return result;
    }
    load.addEventListener('click', function () { file.click(); });
    file.addEventListener('change', function () {
      if (!file.files.length) return;
      file.files[0].text().then(function (text) {
        var result = importDocuments(JSON.parse(text), true);
        if (!result.recognized) showTransfer('No original review marks were found in that file.');
      }).catch(function (error) { showTransfer('Could not load marks: ' + error.message + '. Originals remain untouched.'); });
      file.value = '';
    });
    function origin(host) { return 'http://' + host + ':' + config.sourcePort; }
    function bridgeURL(record, mode) {
      return record.origin + '/' + config.bridge + '?target=' + encodeURIComponent(location.origin) +
             '&nonce=' + encodeURIComponent(record.nonce) + '&mode=' + mode;
    }
    bring.addEventListener('click', function () {
      // A top-level window reads first-party storage even when embedded frames
      // are partitioned or blocked. Try both original local addresses in turn.
      popup = {origin: origin(location.hostname), nonce: nonce(), answered: false, alternate: false};
      popup.window = window.open(bridgeURL(popup, 'popup'), 'original-review-marks', 'popup,width=620,height=360');
      if (!popup.window) showTransfer('Allow the original-review window, or download marks on the original page and load that file here.');
      else showTransfer('Reading marks directly from the original review…');
    });
    window.addEventListener('message', function (event) {
      var frame = frames.find(function (f) { return f.window === event.source && f.origin === event.origin; });
      if (popup && popup.window === event.source && popup.origin === event.origin) frame = popup;
      var message = event.data;
      if (!frame || !message || message.type !== 'probe-edge-review-transfer-v1' ||
          message.nonce !== frame.nonce || message.sourceKey !== config.sourceKey || frame.answered) return;
      frame.answered = true;
      try {
        var result = message.error ? {recognized: 0} : importDocuments(message.documents, frame === popup);
        if (frame === popup && !result.recognized && !frame.alternate) {
          frame.alternate = true; frame.answered = false; frame.nonce = nonce();
          frame.origin = origin(location.hostname === 'localhost' ? '127.0.0.1' : 'localhost');
          frame.window.location = bridgeURL(frame, 'popup');
          return;
        }
        if (frame === popup) event.source.postMessage({type: 'probe-edge-review-transfer-ack', nonce: frame.nonce,
          count: result.recognized}, event.origin);
        if (!recognized && (frame === popup || frames.every(function (f) { return f.answered; })))
          showTransfer('Marks have not transferred. Click Bring original marks, or download them on the original page and load the file here.');
      } catch (e) {
        showTransfer('Transfer could not finish: ' + e.message + '. Originals remain untouched.');
      }
    });
    if (!['127.0.0.1', 'localhost'].includes(location.hostname) || location.port !== String(config.targetPort)) {
      showTransfer('Open this review on localhost port ' + config.targetPort + ' to carry over your original marks.'); return;
    }
    [location.hostname, location.hostname === 'localhost' ? '127.0.0.1' : 'localhost'].forEach(function (host) {
      var element = document.createElement('iframe'); element.hidden = true;
      var record = {origin: origin(host), nonce: nonce(), answered: false, window: null};
      frames.push(record);
      element.src = bridgeURL(record, 'frame');
      document.body.appendChild(element); record.window = element.contentWindow;
    });
    setTimeout(function () {
      if (!recognized && !(popup && !popup.answered))
        showTransfer('Original marks have not transferred. Click Bring original marks above.');
    }, 5000);
  });
'''


def transfer_setup(source_review, source_windows, target_windows, source_port, target_port):
    source_review = Path(source_review)
    match = re.search(r'probe-edge-review:[0-9a-f]{64}', (source_review / 'edges.html').read_text())
    if not match:
        raise ValueError('Original review storage key not found')
    source_key = match.group(0)
    bridge_name = f'edge_marks_to_{target_port}_v2.html'
    bridge = '''<!doctype html><meta charset="utf-8"><title>Original review marks</title>
<style>body{font:18px/1.5 system-ui;margin:28px}button{padding:10px}</style>
<h1>Original review marks</h1><p id="status">Reading saved marks. The original review is unchanged.</p>
<button id="download">Download original marks</button><script>
(() => {
  const query = new URLSearchParams(location.search), target = query.get('target');
  if (!%ORIGINS%.includes(target)) return;
  const message = {type: 'probe-edge-review-transfer-v1', sourceKey: %KEY%, nonce: query.get('nonce')};
  try { message.documents = JSON.parse(localStorage.getItem(message.sourceKey) || '{}'); }
  catch (error) { message.error = 'Original browser storage is unavailable'; }
  const receiver = opener || (parent !== window ? parent : null);
  const count = Object.values(message.documents || {}).reduce((n, doc) => n + (doc.strokes || []).length, 0);
  document.getElementById('status').textContent = count ? 'Found ' + count + ' marks. Sending them to round two…' : 'No marks found at this address. The transfer will also try the alternate original address.';
  document.getElementById('download').onclick = () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(message.documents || {}, null, 2)], {type: 'application/json'}));
    const a = document.createElement('a'); a.href = url; a.download = 'original-edge-marks.json'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  addEventListener('message', event => {
    if (event.source !== receiver || event.origin !== target || !event.data ||
        event.data.type !== 'probe-edge-review-transfer-ack' || event.data.nonce !== message.nonce) return;
    document.getElementById('status').textContent = event.data.count ? 'Original marks delivered. You can return to round two.' : 'No marks were found. Use Download marks in the original review and Load original marks file in round two.';
    if (event.data.count && opener) setTimeout(() => close(), 500);
  });
  if (receiver) receiver.postMessage(message, target);
  else document.getElementById('status').textContent = 'Download original marks below, then use Load original marks file in round two.';
})();
</script>'''.replace('%ORIGINS%', json.dumps([f'http://127.0.0.1:{target_port}', f'http://localhost:{target_port}'])).replace('%KEY%', json.dumps(source_key))
    bridge_path = source_review / bridge_name
    if bridge_path.exists() and bridge_path.read_text() != bridge:
        raise ValueError(f'Refusing to replace existing {bridge_path}')
    bridge_path.write_text(bridge)

    def windows(path):
        return {w['id']: {k: w[k] for k in ('center_enu', 'half', 'mpp')}
                for w in json.loads(Path(path).read_text())}

    config = dict(sourceKey=source_key, sourceWindows=windows(source_windows),
                  targetWindows=windows(target_windows), sourcePort=source_port,
                  targetPort=target_port, bridge=bridge_name)
    library = Path(__file__).with_name('edge_mark_transfer.cjs').read_text()
    return library, TRANSFER.replace('%CONFIG%', json.dumps(config))


def build(src, out, title, intro=None, transfer=None):
    module_path = Path(__file__).with_name('edge_draw_page.py')
    spec = importlib.util.spec_from_file_location('edge_draw_page', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    page, items = module.build(str(src), str(out), title, intro=intro)
    if not items:
        raise SystemExit('No outline images found; no review page can be built.')
    digest = hashlib.sha256()
    for item in items:
        digest.update(item['id'].encode())
        digest.update((Path(out) / item['file']).read_bytes())
    key = 'probe-edge-review:' + digest.hexdigest()
    html = Path(page).read_text(encoding='utf-8')
    # Keep the generator's styles/title in the head and load the adapter before
    # its drawing script. The original generator emits an HTML fragment.
    library, migration = transfer if transfer else ('', '')
    adapter = ('<script>' + library + '</script>' if library else '')
    adapter += ADAPTER.replace('%KEY%', json.dumps(key)).replace('%TRANSFER%', migration)
    html = html.replace('<div class="wrap">', '</head><body>' + adapter + '<div class="wrap">', 1)
    html = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            + html + '</body></html>')
    Path(page).write_text(html, encoding='utf-8')
    return page, items


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--src', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--title', required=True)
    parser.add_argument('--intro-file', type=Path, help='trusted HTML with round-specific findings and review instructions')
    parser.add_argument('--import-review', type=Path, help='original review folder; original HTML and marks are never changed')
    parser.add_argument('--source-windows', type=Path, help='original windows.json for mark registration')
    parser.add_argument('--target-windows', type=Path, help='new windows.json for mark registration')
    parser.add_argument('--source-port', type=int, default=5197)
    parser.add_argument('--target-port', type=int, default=5198)
    args = parser.parse_args()
    intro = args.intro_file.read_text(encoding='utf-8') if args.intro_file else None
    transfer = None
    if args.import_review:
        if not args.source_windows or not args.target_windows:
            parser.error('--import-review needs --source-windows and --target-windows')
        transfer = transfer_setup(args.import_review, args.source_windows, args.target_windows,
                                  args.source_port, args.target_port)
    page, items = build(args.src, args.out, args.title, intro=intro, transfer=transfer)
    print(f'{len(items)} windows -> {page}; local browser storage + Download marks')


if __name__ == '__main__':
    main()
