// 分析截图：定位饼图圆环（连通域过滤掉图例圆点），测量中心文字与圆心偏差
const fs = require("fs");
const { PNG } = require("pngjs");

const RING_COLORS = [
  [0xff, 0x6b, 0x6b], [0xff, 0xa9, 0x4d], [0xff, 0xd4, 0x3b], [0x69, 0xdb, 0x7c],
  [0x74, 0xc0, 0xfc], [0xda, 0x77, 0xf2], [0x4d, 0xab, 0xf7],
];
const TOL = 14;

function analyze(path, label) {
  if (!fs.existsSync(path)) { console.log(label + ": FILE MISSING"); return; }
  const png = PNG.sync.read(fs.readFileSync(path));
  const { width: W, height: H, data } = png;

  // 1) 标记彩色像素
  const ringMask = new Uint8Array(W * H);
  const darkMask = new Uint8Array(W * H);
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 4;
      const r = data[i], g = data[i + 1], b = data[i + 2];
      if (ringMask[y * W + x] === 0) {
        for (const [cr, cg, cb] of RING_COLORS) {
          if (Math.abs(r - cr) <= TOL && Math.abs(g - cg) <= TOL && Math.abs(b - cb) <= TOL) { ringMask[y * W + x] = 1; break; }
        }
      }
      if (r < 80 && g < 80 && b < 80) darkMask[y * W + x] = 1;
    }
  }

  // 2) 连通域（4 邻接），只保留大块（圆弧），图例圆点会被过滤
  const seen = new Uint8Array(W * H);
  const comps = [];
  const stack = [];
  for (let s = 0; s < W * H; s++) {
    if (!ringMask[s] || seen[s]) continue;
    seen[s] = 1;
    stack.length = 0;
    stack.push(s);
    const pts = [];
    while (stack.length) {
      const c = stack.pop();
      pts.push(c);
      const x = c % W, y = (c / W) | 0;
      if (x > 0 && ringMask[c - 1] && !seen[c - 1]) { seen[c - 1] = 1; stack.push(c - 1); }
      if (x < W - 1 && ringMask[c + 1] && !seen[c + 1]) { seen[c + 1] = 1; stack.push(c + 1); }
      if (y > 0 && ringMask[c - W] && !seen[c - W]) { seen[c - W] = 1; stack.push(c - W); }
      if (y < H - 1 && ringMask[c + W] && !seen[c + W]) { seen[c + W] = 1; stack.push(c + W); }
    }
    comps.push(pts);
  }
  comps.sort((a, b) => b.length - a.length);
  const big = comps.filter((c) => c.length > 1500);
  if (big.length === 0) { console.log(label + ": no ring arcs found; comps:", comps.slice(0, 8).map((c) => c.length).join(",")); return; }
  const ringPts = [].concat(...big);
  let cx = 0, cy = 0;
  for (const c of ringPts) { cx += c % W; cy += (c / W) | 0; }
  cx /= ringPts.length; cy /= ringPts.length;
  let rIn = Infinity, rOut = 0;
  for (const c of ringPts) {
    const x = c % W, y = (c / W) | 0;
    const d = Math.hypot(x - cx, y - cy);
    if (d < rIn) rIn = d;
    if (d > rOut) rOut = d;
  }

  // 3) 圆环内径范围内的深色文字
  const textPts = [];
  for (let s = 0; s < W * H; s++) {
    if (!darkMask[s]) continue;
    const x = s % W, y = (s / W) | 0;
    if (Math.hypot(x - cx, y - cy) < rIn * 0.95) textPts.push([x, y]);
  }
  if (textPts.length < 10) { console.log(label + ": no text in hole (arcPx=" + ringPts.length + " comps=" + big.length + ")"); return; }
  let tx0 = Infinity, ty0 = Infinity, tx1 = -Infinity, ty1 = -Infinity;
  for (const [x, y] of textPts) {
    if (x < tx0) tx0 = x; if (x > tx1) tx1 = x;
    if (y < ty0) ty0 = y; if (y > ty1) ty1 = y;
  }
  const tx = (tx0 + tx1) / 2, ty = (ty0 + ty1) / 2;

  console.log("===== " + label + " =====");
  console.log("image: " + W + "x" + H + "  arcs=" + big.length + "  arcPx=" + ringPts.length + "  textPx=" + textPts.length);
  console.log("ring center: (" + cx.toFixed(1) + ", " + cy.toFixed(1) + ")  rIn=" + rIn.toFixed(1) + "  rOut=" + rOut.toFixed(1) + "  holeD=" + (rIn * 2).toFixed(0) + "px");
  console.log("text bbox: (" + tx0 + "," + ty0 + ")-(" + tx1 + "," + ty1 + ")  w=" + (tx1 - tx0) + " h=" + (ty1 - ty0) + "  center=(" + tx.toFixed(1) + ", " + ty.toFixed(1) + ")");
  console.log("TEXT-vs-RING delta (physical px): dx=" + (tx - cx).toFixed(2) + "  dy=" + (ty - cy).toFixed(2));
}

analyze("C:/work/bookkeeping/shot_ref_175.png", "reference headless 175%");
if (fs.existsSync("C:/work/bookkeeping/shot_normal.png")) analyze("C:/work/bookkeeping/shot_normal.png", "user normal window");
if (fs.existsSync("C:/work/bookkeeping/shot_max.png")) analyze("C:/work/bookkeeping/shot_max.png", "user maximized (fullscreen)");
if (fs.existsSync("C:/work/bookkeeping/shot_info.txt")) {
  console.log("----- shot_info.txt -----");
  console.log(fs.readFileSync("C:/work/bookkeeping/shot_info.txt", "utf8"));
}
