const {test} = require('node:test');
const assert = require('node:assert/strict');
const {project, merge, dimensions} = require('./edge_mark_transfer.cjs');

const oldWindow = {center_enu: [100, 200], half: 75, mpp: 0.12};
const newWindow = {center_enu: [102, 197], half: 40, mpp: 0.06};
const line = {c: 'red', kind: 'line', pts: [[-20, 80], [600, 900]], ctrl: [[-20, 80], [600, 900]]};
function world(point, window) {
  return [window.center_enu[0] - window.half + point[0] * window.mpp,
          window.center_enu[1] + window.half - point[1] * window.mpp];
}
function near(a, b) { a.forEach((v, i) => assert.ok(Math.abs(v - b[i]) < 1e-10)); }

test('marks and edit handles retain their world positions across different crops and scales', () => {
  const before = JSON.stringify(line), result = project(line, oldWindow, newWindow);
  result.pts.forEach((p, i) => near(world(p, newWindow), world(line.pts[i], oldWindow)));
  result.ctrl.forEach((p, i) => near(world(p, newWindow), world(line.ctrl[i], oldWindow)));
  assert.equal(JSON.stringify(line), before);
});

test('carry-over merges with round-two work and never mutates either source', () => {
  const existingMark = {c: 'green', kind: 'free', pts: [[10, 20], [30, 40]]};
  const existing = {w_s0000: {...dimensions(newWindow), strokes: [existingMark], at: 'user-edit'}};
  const source = {w_s0000: {...dimensions(oldWindow), strokes: [line]}};
  const before = JSON.stringify({existing, source});
  const result = merge(existing, source, [], {w_s0000: oldWindow}, {w_s0000: newWindow}, 'round-one');
  assert.equal(result.added, 1);
  assert.equal(result.records.w_s0000.strokes.length, 2);
  assert.deepEqual(result.records.w_s0000.strokes[0], existingMark);
  assert.equal(result.records.w_s0000.at, 'user-edit');
  assert.equal(JSON.stringify({existing, source}), before);
});

test('reloads do not duplicate imported marks or resurrect marks the user erased', () => {
  const source = {w_s0000: {...dimensions(oldWindow), strokes: [line]}};
  const sourceWindows = {w_s0000: oldWindow}, targetWindows = {w_s0000: newWindow};
  const first = merge({}, source, [], sourceWindows, targetWindows, 'round-one');
  const second = merge(first.records, source, first.imports, sourceWindows, targetWindows, 'round-one');
  assert.equal(second.added, 0);
  assert.equal(second.records.w_s0000.strokes.length, 1);
  const erased = {w_s0000: {...dimensions(newWindow), strokes: []}};
  const afterErase = merge(erased, source, first.imports, sourceWindows, targetWindows, 'round-one');
  assert.equal(afterErase.records.w_s0000.strokes.length, 0);
});

test('mismatched source image metadata fails without modifying current marks', () => {
  const existing = {w_s0000: {...dimensions(newWindow), strokes: [line]}};
  const before = JSON.stringify(existing);
  assert.throws(() => merge(existing, {w_s0000: {w: 1, h: 1, strokes: [line]}}, [],
                           {w_s0000: oldWindow}, {w_s0000: newWindow}, 'round-one'), /dimensions/);
  assert.equal(JSON.stringify(existing), before);
});
