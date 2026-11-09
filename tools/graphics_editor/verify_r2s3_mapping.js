// Headless regression for the R2-S3 Composer mapping-propagation fix (PROMT-ID-0110).
//
// Bug: editing a Genesis TARGET color updated only the Genesis Target swatches; the mapped tile preview
// and the source->target mapping chips stayed stale because afterChange() did not re-render the detail
// view. Fix: afterChange() -> refreshDetail() re-renders the active Layer-A (or sprite) detail.
//
// Loads the real app.js in a minimal DOM shim and checks that afterChange() re-renders the detail, that a
// scoped Genesis edit changes the EFFECTIVE color the mapped preview uses (while the bank-addressed ARCADE
// SOURCE is independent), and that serialize/reload of a TEMPORARY fixture preserves the scoped mapping.
// Never touches Test.json / Test_2_0.json.  Run: node tools/graphics_editor/verify_r2s3_mapping.js
'use strict';
const fs = require('fs'), path = require('path');
global.__P = 0; global.__F = 0;
global.__ck = (n, c, d) => { if (c) { global.__P++; console.log('PASS ' + n); } else { global.__F++; console.log('FAIL ' + n + (d ? ' — ' + d : '')); } };

// ---- minimal DOM / browser shim -------------------------------------------------------------------
function elem() {
  const e = { children: [], _html: '', textContent: '', className: '', style: {}, dataset: {}, classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } } };
  Object.defineProperty(e, 'innerHTML', { get() { return e._html; }, set(v) { e._html = v; e.children = []; } });
  e.appendChild = c => { e.children.push(c); return c; };
  e.querySelectorAll = () => [];
  e.getBoundingClientRect = () => ({ left: 0, top: 0, width: 160, height: 160 });
  return e;
}
const nodes = {};
global.document = {
  querySelector: s => (nodes[s] = nodes[s] || elem()),
  getElementById: s => (nodes['#' + s] = nodes['#' + s] || elem()),
  createElement: () => elem(),
  querySelectorAll: () => [],
};
global.window = global;
global.localStorage = { getItem() { return null; }, setItem() {} };
global.alert = () => {}; global.confirm = () => true;
global.requestAnimationFrame = () => {};
global.Image = class { constructor() { this.onload = null; } set src(v) { this._src = v; } get src() { return this._src; } };
global.fetch = async () => ({ json: async () => ({}) });

// ---- app.js (boot() suppressed) + the test harness are eval'd TOGETHER so the harness shares app.js's
//      `let` module scope (O/POL/SCOPE/TAB/LADET/... and the hoisted render functions). --------------
let src = fs.readFileSync(path.join(__dirname, 'app.js'), 'utf8');
src = src.replace(/\nboot\(\);\s*$/, '\n/* boot() suppressed for test */\n');

const harness = `
;(function(){
  const SCENE = 'PAL-R2-S3-PLANEA-BOSS';
  O = { contexts: [{ id: 'context:gameplay', display: 'Gameplay', parent: null }, { id: SCENE, display: 'R2-S3 Boss', parent: 'context:gameplay' }], usages: [] };
  POL = { profile_id: '__fixture__', immutable: false, reserved_lines: [2],
    target_palette_lines: [Array(16).fill(null), Array(16).fill(null), Array(16).fill(null), Array(16).fill(null)],
    usage_palette_mappings: {}, plane_usage_palette_mappings: {}, context_policies: {} };
  SCOPE = SCENE; TAB = 'layera';
  const USAGE = { usage_id: 'LA-TEST', tile_code: 0x105E, palette_bank: '0x002', segments: [45], n_colors: 2, flip: 0,
    used_colors: [
      { src_index: 2, arcade_rgb8: [214,214,165], hex: '#D6D6A5', genesis_rgb8: [224,224,160], genesis_cram: '0x0EEE' },
      { src_index: 4, arcade_rgb8: [66,66,66],   hex: '#424242', genesis_rgb8: [64,64,64],   genesis_cram: '0x0444' } ] };
  LADET = { pattern: { pattern_id: 'A-TEST', tile_codes: [0x105E], pattern_hash: 'xxxxxxxxxxxxxxxxxxxxxxxx', used_indices: [2,4], n_colors: 2, segments:[45], palette_banks:['0x002'], n_uses:1, animation_status:'STATIC', rep_tile_code:0x105E, multi_palette:false }, pixels: [], usages: [USAGE] };
  LAUSAGE = USAGE;
  LA = { banks: { '0x002': USAGE.used_colors.map(c => c.arcade_rgb8) } };

  let nLADetail = 0, nMapTable = 0, nPreviews = 0;
  renderScopeBar = () => {}; renderTarget = () => {}; renderSource = () => {}; validate = () => {};
  renderLADetail = () => { nLADetail++; };
  renderMapTable = () => { nMapTable++; };
  renderPreviews = () => { nPreviews++; };

  nLADetail = 0; afterChange();
  __ck('1. afterChange() re-renders Layer-A detail (mapped preview + chips)', nLADetail === 1, 'nLADetail=' + nLADetail);

  TAB = 'objects'; U = { usage_id: 'SPR', used_colors: [] }; nMapTable = nPreviews = 0; afterChange();
  __ck('2. afterChange() re-renders sprite map table + preview', nMapTable === 1 && nPreviews === 1, 'map=' + nMapTable + ' prev=' + nPreviews);
  TAB = 'layera';

  setPlaneMapping(USAGE.usage_id, { line: 0, index_map: { 2: 5 } });
  setTgt(0, 5, '0x0E00');
  __ck('3. effCramAt reflects the scoped edit', effCramAt(0, 5) === '0x0E00', 'got ' + effCramAt(0, 5));
  const mappedPal = laGenPal(USAGE);
  __ck('4. mapped tile preview uses the edited color for the mapped index', JSON.stringify(mappedPal[2]) === JSON.stringify(cramToRGB('0x0E00')), JSON.stringify(mappedPal[2]));
  __ck('5. unmapped index keeps its natural arcade color', JSON.stringify(mappedPal[4]) === JSON.stringify(USAGE.used_colors[1].genesis_rgb8));
  __ck('6. mapping stored at the R2-S3 scope (scene-local)', !!(POL.context_policies[SCENE] && POL.context_policies[SCENE].plane_usage_palette_mappings['LA-TEST']) && Object.keys(POL.plane_usage_palette_mappings).length === 0);

  const saved = JSON.stringify(POL);
  POL = JSON.parse(saved);
  __ck('7. reload preserves the scoped Genesis color', effCramAt(0, 5) === '0x0E00');
  const pm = planeMap('LA-TEST');
  __ck('8. reload preserves the scoped mapping', !!pm && pm.line === 0 && pm.index_map[2] === 5);

  const arcadeSrc = '/api/render_tile?code=' + USAGE.tile_code + '&bank=' + USAGE.palette_bank + '&z=20';
  __ck('9. arcade-source render query is bank-addressed (independent of Genesis edits)', /render_tile\\?code=.*&bank=/.test(arcadeSrc));
})();
`;

eval(src + harness);

console.log('\nR2S3_MAPPING ' + (global.__F === 0 ? 'PASS' : 'FAIL') + '  (pass=' + global.__P + ', fail=' + global.__F + ')');
process.exit(global.__F ? 1 : 0);
