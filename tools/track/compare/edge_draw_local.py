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
The old page and its storage remain unchanged. A read-only bridge at its origin
copies marks through their ENU coordinates when the new page loads, merging
with existing new marks. Ports default to 5197 (source) and 5198 (target).
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
    var config = %CONFIG%, frames = [], imported = 0, recognized = 0, answered = 0;
    var ledgerKey = key + ':imports', ledger = [];
    try { ledger = JSON.parse(localStorage.getItem(ledgerKey) || '[]'); }
    catch (e) { showTransfer('Could not read transfer history; originals remain untouched.'); return; }
    function showTransfer(message) {
      var banner = document.getElementById('banner');
      banner.textContent = message; banner.classList.add('show');
    }
    window.addEventListener('message', function (event) {
      var frame = frames.find(function (f) { return f.window === event.source && f.origin === event.origin; });
      var message = event.data;
      if (!frame || !message || message.type !== 'probe-edge-review-transfer-v1' ||
          message.nonce !== frame.nonce || message.sourceKey !== config.sourceKey || frame.answered) return;
      frame.answered = true; answered++;
      if (message.error) {
        if (!imported && !recognized) showTransfer('Original marks could not be read here. Open this page in the same browser used for round one.');
        return;
      }
      try {
        var result = EdgeMarkTransfer.merge(records, message.documents || {}, ledger,
                                             config.sourceWindows, config.targetWindows, config.sourceKey);
        if (result.recognized) {
          // Write marks first, then publish to the drawing UI. A ledger failure
          // must never leave the UI holding an older copy that can erase marks.
          localStorage.setItem(key, JSON.stringify(result.records));
          records = result.records; ledger = result.imports; notify();
          imported += result.added; recognized += result.recognized;
          try { localStorage.setItem(ledgerKey, JSON.stringify(ledger)); }
          catch (e) { showTransfer('Marks carried over, but transfer history could not be saved. Download marks as a backup.'); return; }
        }
        if (imported) showTransfer('Carried over ' + imported + ' original mark' + (imported === 1 ? '' : 's') + '. Originals and existing round-two marks are preserved.');
        else if (recognized) showTransfer('Your original marks have already been carried over. Existing round-two edits are preserved.');
        else if (answered === frames.length) showTransfer('No original marks were found here. Open this page in the same browser and hostname used for round one.');
      } catch (e) {
        showTransfer('Transfer could not finish (' + e.message + '). Originals remain untouched.');
      }
    });
    if (!['127.0.0.1', 'localhost'].includes(location.hostname) || location.port !== String(config.targetPort)) {
      showTransfer('Open this review on localhost port ' + config.targetPort + ' to carry over your original marks.'); return;
    }
    // Try the current hostname first; localhost and 127.0.0.1 have separate
    // browser stores. Each bridge reads only the known original review key.
    [location.hostname, location.hostname === 'localhost' ? '127.0.0.1' : 'localhost'].forEach(function (host) {
      var origin = 'http://' + host + ':' + config.sourcePort;
      var nonce = crypto.randomUUID();
      var element = document.createElement('iframe'); element.hidden = true;
      var record = {origin: origin, nonce: nonce, answered: false, window: null};
      frames.push(record);
      element.src = origin + '/' + config.bridge + '?target=' + encodeURIComponent(location.origin) + '&nonce=' + encodeURIComponent(nonce);
      document.body.appendChild(element); record.window = element.contentWindow;
    });
  });
'''


def transfer_setup(source_review, source_windows, target_windows, source_port, target_port):
    source_review = Path(source_review)
    match = re.search(r'probe-edge-review:[0-9a-f]{64}', (source_review / 'edges.html').read_text())
    if not match:
        raise ValueError('Original review storage key not found')
    source_key = match.group(0)
    bridge_name = f'edge_marks_to_{target_port}.html'
    bridge = '''<!doctype html><meta charset="utf-8"><script>
(() => {
  const query = new URLSearchParams(location.search), target = query.get('target');
  if (!%ORIGINS%.includes(target) || parent === window) return;
  const message = {type: 'probe-edge-review-transfer-v1', sourceKey: %KEY%, nonce: query.get('nonce')};
  try { message.documents = JSON.parse(localStorage.getItem(message.sourceKey) || '{}'); }
  catch (error) { message.error = 'Original browser storage is unavailable'; }
  parent.postMessage(message, target);
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
