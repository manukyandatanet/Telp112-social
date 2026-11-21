// usage: node render.js spec.json OUT.mp4   (run from repo root; paths in spec relative to repo root)
// Renders brand/promo/promo.html frame by frame (30 fps) with Playwright, then encodes with ffmpeg.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execSync } = require('child_process');
(async () => {
  const [specPath, out] = process.argv.slice(2);
  const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
  const root = process.cwd();
  const abs = p => 'file://' + path.resolve(root, p);
  spec.logo = abs(spec.logo || 'brand/logo.png');
  spec.scenes.forEach(s => { if (s.photo) s.photo = abs(s.photo); if (s.icon) s.icon = fs.readFileSync(path.join(__dirname, 'icons', s.icon + '.svg'), 'utf8').replace(/<!--.*?-->/s, ''); });
  const total = spec.scenes.reduce((a, s) => a + s.dur, 0);
  const fps = 30, n = Math.round(total * fps);
  const tmp = fs.mkdtempSync(path.join(require('os').tmpdir(), 'promo-'));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(__dirname, 'promo.html'));
  await page.evaluate(s => window.setup(s), spec);
  await page.waitForTimeout(500);
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => window.renderAt(t), i / fps);
    await page.screenshot({ path: path.join(tmp, `f${String(i).padStart(4, '0')}.jpg`), type: 'jpeg', quality: 92 });
  }
  await browser.close();
  execSync(`python3 ${path.join(__dirname, 'sound.py')} ${specPath} ${tmp}/a.wav`);
  execSync(`ffmpeg -v error -y -framerate ${fps} -i ${tmp}/f%04d.jpg -i ${tmp}/a.wav -shortest -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart ${out}`);
  fs.rmSync(tmp, { recursive: true });
  console.log(out, total + 's', n + ' frames');
})();
