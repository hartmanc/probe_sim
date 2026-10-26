#!/usr/bin/env python3
"""Build the existing edge drawing page for local review without an Artifact DB.

    python3 -I tools/track/compare/edge_draw_local.py --src <outline-dir> \
        --out <review-dir> --title 'Mid-Ohio edge review'

Serve the result over localhost. Marks persist in that browser, keyed to the
actual window images. Download marks before changing browser or server origin.
The downloaded JSON maps window IDs to the same per-window documents consumed
by edge_draw_render.py; split them into files there before rendering.
Reference images remain local and must never be committed or used as textures.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


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


def build(src, out, title, intro=None):
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
    adapter = ADAPTER.replace('%KEY%', json.dumps(key))
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
    args = parser.parse_args()
    intro = args.intro_file.read_text(encoding='utf-8') if args.intro_file else None
    page, items = build(args.src, args.out, args.title, intro=intro)
    print(f'{len(items)} windows -> {page}; local browser storage + Download marks')


if __name__ == '__main__':
    main()
