/* Transfer review strokes through their north-up ENU window coordinates. */
(function (root) {
  'use strict';
  function identity(stroke) {
    return JSON.stringify([stroke.c, stroke.kind || 'free', stroke.pts, stroke.ctrl || null]);
  }
  function dimensions(window) {
    const size = Math.floor(2 * window.half / window.mpp);
    return {w: size, h: size, margin: Math.round(0.1 * size)};
  }
  function project(stroke, source, target) {
    function point(p) {
      if (!Array.isArray(p) || p.length !== 2 || !p.every(Number.isFinite)) {
        throw new Error('Invalid mark coordinates');
      }
      const x = source.center_enu[0] - source.half + p[0] * source.mpp;
      const y = source.center_enu[1] + source.half - p[1] * source.mpp;
      return [(x - target.center_enu[0] + target.half) / target.mpp,
              (target.center_enu[1] + target.half - y) / target.mpp];
    }
    if (!['red', 'green'].includes(stroke.c) || !Array.isArray(stroke.pts) || !stroke.pts.length) {
      throw new Error('Invalid review mark');
    }
    const result = Object.assign({}, stroke, {pts: stroke.pts.map(point)});
    if (stroke.ctrl) result.ctrl = stroke.ctrl.map(point);
    return result;
  }
  function merge(existing, documents, previousImports, sourceWindows, targetWindows, sourceKey) {
    const records = Object.assign({}, existing);
    const seen = new Set(previousImports);
    let added = 0, importedWindows = 0, recognized = 0;
    for (const [id, target] of Object.entries(targetWindows)) {
      const source = sourceWindows[id], document = documents[id];
      if (!source || !document || !Array.isArray(document.strokes)) continue;
      const size = dimensions(target), originalSize = dimensions(source);
      if (document.w !== originalSize.w || document.h !== originalSize.h) {
        throw new Error('Original image dimensions do not match ' + id);
      }
      const current = records[id];
      if (current && (current.w !== size.w || current.h !== size.h)) {
        throw new Error('Existing round-two image dimensions do not match ' + id);
      }
      const strokes = current ? current.strokes.slice() : [];
      const present = new Set(strokes.map(identity));
      let windowAdded = 0;
      document.strokes.forEach(function (stroke, index) {
        recognized++;
        // The full source identity avoids collisions and remembers deliberately
        // erased imports, so a reload never puts a deleted stroke back.
        const importId = JSON.stringify([sourceKey, id, index, identity(stroke)]);
        if (seen.has(importId)) return;
        const transformed = project(stroke, source, target);
        const fingerprint = identity(transformed);
        if (!present.has(fingerprint)) {
          strokes.push(transformed); present.add(fingerprint);
          added++; windowAdded++;
        }
        seen.add(importId);
      });
      if (windowAdded) {
        importedWindows++;
        records[id] = Object.assign({}, current || {}, size, {strokes: strokes});
      }
    }
    return {records: records, imports: Array.from(seen), added: added,
            windows: importedWindows, recognized: recognized};
  }
  const api = {project: project, merge: merge, dimensions: dimensions};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.EdgeMarkTransfer = api;
})(globalThis);
