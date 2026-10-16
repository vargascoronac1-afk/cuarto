const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const R = __dirname, K = process.argv[2], OUT = process.argv[3];
const T = path.join(R, '..', 't', 'node_modules', 'three');
const files = {
  'render.html': [path.join(R, 'render.html'), 'text/html'],
  'three.min.js': [path.join(T, 'build/three.min.js'), 'text/javascript'],
  'STLLoader.js': [path.join(T, 'examples/js/loaders/STLLoader.js'), 'text/javascript'],
};
for (const f of ['vista_izq.stl', 'vista_der.stl', 'vista_mon_izq.stl', 'vista_mon_der.stl']) files[f] = [path.join(K, f), 'application/octet-stream'];
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1600, height: 1000 } });
  const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p.route('http://render.local/**', r => { const n = r.request().url().split('/').pop(); const f = files[n]; if (!f) return r.fulfill({ status: 404 }); r.fulfill({ body: fs.readFileSync(f[0]), contentType: f[1] }); });
  await p.goto('http://render.local/render.html');
  await p.evaluate(() => window.ready);
  for (const s of ['general', 'cerca', 'pieza', 'frente']) {
    await p.evaluate(n => window.shot(n), s);
    await p.locator('canvas').screenshot({ path: path.join(OUT, s + '.png') });
  }
  console.log(JSON.stringify(errs)); await b.close();
})();
