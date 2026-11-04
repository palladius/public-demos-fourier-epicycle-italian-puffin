# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent

import json

with open("assets/fourier_2049_coeffs.json", "r") as f:
    fdata = json.load(f)

# Compact the 2049 coefficients to [k, round(re,3), round(im,3), round(amp,3)] to keep the HTML super fast & light
compact_coeffs = [[c[0], round(c[1], 3), round(c[2], 3), round(c[3], 3)] for c in fdata["coeffs"]]

html_content = f"""<!--
 Copyright 2026 Google LLC
 SPDX-License-Identifier: Apache-2.0
-->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Italian Puffin in a Google Tri-Suit — 2,049 Fourier Epicycles (Gemini × Lyria 3.5)</title>
  <style>
    :root {{
      --bg: #07080c;
      --panel: rgba(12, 16, 26, 0.88);
      --border: rgba(66, 133, 244, 0.45);
      --g-blue: #4285F4;
      --g-red: #EA4335;
      --g-yellow: #FBBC05;
      --g-green: #34A853;
      --text: #e8f0fe;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
      overflow-x: hidden;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      padding: 18px;
    }}
    header {{
      max-width: 1280px;
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 20px;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 10px;
      margin-bottom: 14px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.6);
    }}
    .title-group h1 {{
      font-size: 1.15rem;
      letter-spacing: 0.04em;
      color: #fff;
    }}
    .title-group p {{
      font-size: 0.78rem;
      color: #8ab4f8;
      margin-top: 4px;
    }}
    .google-dots {{
      display: flex;
      gap: 8px;
      align-items: center;
    }}
    .dot {{
      width: 14px;
      height: 14px;
      border-radius: 50%;
      display: inline-block;
    }}
    .stage-wrap {{
      position: relative;
      max-width: 1280px;
      width: 100%;
      aspect-ratio: 16 / 9;
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      background: #07080c;
      box-shadow: 0 12px 48px rgba(0, 0, 0, 0.85);
    }}
    canvas {{
      width: 100%;
      height: 100%;
      display: block;
    }}
    .controls {{
      max-width: 1280px;
      width: 100%;
      margin-top: 14px;
      padding: 16px 22px;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 10px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      align-items: center;
    }}
    .ctrl-box {{
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .ctrl-box label {{
      font-size: 0.78rem;
      color: #9aa0a6;
      display: flex;
      justify-content: space-between;
    }}
    .ctrl-box label span {{
      color: #fff;
      font-weight: bold;
    }}
    input[type="range"] {{
      width: 100%;
      accent-color: var(--g-blue);
      cursor: pointer;
    }}
    .btn-row {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }}
    button {{
      background: rgba(66, 133, 244, 0.18);
      color: #fff;
      border: 1px solid var(--g-blue);
      padding: 9px 14px;
      border-radius: 6px;
      font-family: inherit;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    button:hover {{
      background: var(--g-blue);
      color: #000;
    }}
    button.active {{
      background: var(--g-green);
      border-color: var(--g-green);
      color: #000;
    }}
  </style>
</head>
<body>
  <header>
    <div class="title-group">
      <h1>🐧🚴‍♂️🇮🇹 ITALIAN PUFFIN IN A GOOGLE TRI-SUIT // 2,049 FOURIER EPICYCLES</h1>
      <p>Inspired by @fofrAI • Built with Gemini &amp; Google Lyria 3.5 Cinematic Audio Sync</p>
    </div>
    <div class="google-dots">
      <span class="dot" style="background:#4285F4" title="Google Blue (#4285F4)"></span>
      <span class="dot" style="background:#EA4335" title="Google Red (#EA4335)"></span>
      <span class="dot" style="background:#FBBC05" title="Google Yellow (#FBBC05)"></span>
      <span class="dot" style="background:#34A853" title="Google Green (#34A853)"></span>
    </div>
  </header>

  <div class="stage-wrap">
    <canvas id="fourierCanvas" width="1920" height="1080"></canvas>
  </div>

  <div class="controls">
    <div class="btn-row">
      <button id="playBtn">▶ Play Choreography + Lyria 3.5</button>
      <button id="modeBtn" class="active">Auto Slow-Reveal: ON</button>
      <button id="colorBtn">🎨 Reveal Google Tri-Suit Colors</button>
    </div>
    <div class="ctrl-box">
      <label>Harmonic Circles (M): <span id="mVal">2,049</span></label>
      <input type="range" id="mSlider" min="2" max="2049" value="7" />
    </div>
    <div class="ctrl-box">
      <label>Timeline / Audio Scrub (s): <span id="tVal">0.00s</span></label>
      <input type="range" id="tSlider" min="0" max="30.7" step="0.05" value="0" />
    </div>
  </div>

  <audio id="lyriaAudio" src="../assets/soundtrack_lyria35.mp3" preload="auto"></audio>

  <script>
    const COEFFS = {json.dumps(compact_coeffs)};
    const CX_ORIG = {fdata["center"][0]};
    const CY_ORIG = {fdata["center"][1]};
    const SCALE = 1.26;
    const OFF_X = (1920 - 1408 * SCALE) * 0.5 - 30.0;
    const OFF_Y = (1080 - 768 * SCALE) * 0.5 - 10.0;

    const canvas = document.getElementById('fourierCanvas');
    const ctx = canvas.getContext('2d');
    const audio = document.getElementById('lyriaAudio');

    const imgMono = new Image(); imgMono.src = '../assets/layer_mono.png';
    const imgBlue = new Image(); imgBlue.src = '../assets/layer_google_blue.png';
    const imgRed = new Image(); imgRed.src = '../assets/layer_google_red.png';
    const imgYellow = new Image(); imgYellow.src = '../assets/layer_google_yellow.png';
    const imgGreen = new Image(); imgGreen.src = '../assets/layer_google_green.png';
    const imgAccents = new Image(); imgAccents.src = '../assets/layer_italia_accents.png';

    let autoReveal = true;
    let manualColorReveal = false;
    let simTime = 0.0;
    let lastFrameTime = performance.now();
    let isPlaying = false;

    const playBtn = document.getElementById('playBtn');
    const modeBtn = document.getElementById('modeBtn');
    const colorBtn = document.getElementById('colorBtn');
    const mSlider = document.getElementById('mSlider');
    const tSlider = document.getElementById('tSlider');
    const mVal = document.getElementById('mVal');
    const tVal = document.getElementById('tVal');

    playBtn.addEventListener('click', () => {{
      if (audio.paused) {{
        audio.play();
        isPlaying = true;
        playBtn.textContent = '⏸ Pause Soundtrack';
      }} else {{
        audio.pause();
        isPlaying = false;
        playBtn.textContent = '▶ Play Choreography + Lyria 3.5';
      }}
    }});

    modeBtn.addEventListener('click', () => {{
      autoReveal = !autoReveal;
      modeBtn.classList.toggle('active', autoReveal);
      modeBtn.textContent = autoReveal ? 'Auto Slow-Reveal: ON' : 'Manual Slider Mode';
    }});

    colorBtn.addEventListener('click', () => {{
      manualColorReveal = !manualColorReveal;
      colorBtn.classList.toggle('active', manualColorReveal);
    }});

    mSlider.addEventListener('input', () => {{
      autoReveal = false;
      modeBtn.classList.remove('active');
      modeBtn.textContent = 'Manual Slider Mode';
    }});

    tSlider.addEventListener('input', () => {{
      simTime = parseFloat(tSlider.value);
      if (!audio.paused) audio.currentTime = simTime;
    }});

    function smoothstep(e0, e1, x) {{
      const t = Math.max(0, Math.min(1, (x - e0) / (e1 - e0)));
      return t * t * (3 - 2 * t);
    }}

    // Precompute total AC variance for error %
    let totalVar = 0;
    for (let i = 1; i < COEFFS.length; i++) {{
      totalVar += COEFFS[i][1]*COEFFS[i][1] + COEFFS[i][2]*COEFFS[i][2];
    }}

    let trail = [];

    function render(now) {{
      const dt = (now - lastFrameTime) / 1000.0;
      lastFrameTime = now;

      if (!audio.paused) {{
        simTime = audio.currentTime;
        tSlider.value = simTime;
      }} else {{
        simTime = (simTime + dt * 0.65) % 30.7;
      }}
      tVal.textContent = simTime.toFixed(2) + 's';

      let M = parseInt(mSlider.value, 10);
      if (autoReveal) {{
        if (simTime >= 19.6) {{
          M = 2049;
        }} else {{
          const u = Math.max(0, Math.min(1, simTime / 19.6));
          M = Math.max(2, Math.min(2049, Math.round(2 * Math.pow(1024.5, u * u * (3 - 2 * u)))));
        }}
        mSlider.value = M;
      }}
      mVal.textContent = M.toLocaleString();

      // Compute L2 approximation error
      let capVar = 0;
      for (let i = 1; i < M; i++) {{
        capVar += COEFFS[i][1]*COEFFS[i][1] + COEFFS[i][2]*COEFFS[i][2];
      }}
      const errPct = Math.max(0.12, 100 * Math.sqrt(Math.max(0, totalVar - capVar) / totalVar));

      ctx.fillStyle = '#07080c';
      ctx.fillRect(0, 0, 1920, 1080);

      // Subtle blueprint grid
      ctx.strokeStyle = 'rgba(66, 133, 244, 0.08)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let x = 120; x < 1920; x += 120) {{ ctx.moveTo(x, 0); ctx.lineTo(x, 1080); }}
      for (let y = 120; y < 1080; y += 120) {{ ctx.moveTo(0, y); ctx.lineTo(1920, y); }}
      ctx.stroke();

      // Draw underlying monochrome & Google 4-Color Tri-Suit layers
      const monoAlpha = manualColorReveal ? 1.0 : smoothstep(13.5, 19.5, simTime);
      if (monoAlpha > 0.01 && imgMono.complete) {{
        ctx.save();
        ctx.translate(OFF_X, OFF_Y);
        ctx.scale(SCALE, SCALE);
        ctx.globalAlpha = monoAlpha;
        ctx.drawImage(imgMono, 0, 0);

        const aBlue   = manualColorReveal ? 1.0 : smoothstep(20.0, 21.1, simTime);
        const aRed    = manualColorReveal ? 1.0 : smoothstep(21.1, 22.2, simTime);
        const aYellow = manualColorReveal ? 1.0 : smoothstep(22.2, 23.3, simTime);
        const aGreen  = manualColorReveal ? 1.0 : smoothstep(23.3, 24.4, simTime);
        const aAcc    = manualColorReveal ? 1.0 : smoothstep(24.4, 25.6, simTime);

        if (aBlue > 0.01 && imgBlue.complete)   {{ ctx.globalAlpha = aBlue; ctx.drawImage(imgBlue, 0, 0); }}
        if (aRed > 0.01 && imgRed.complete)     {{ ctx.globalAlpha = aRed; ctx.drawImage(imgRed, 0, 0); }}
        if (aYellow > 0.01 && imgYellow.complete) {{ ctx.globalAlpha = aYellow; ctx.drawImage(imgYellow, 0, 0); }}
        if (aGreen > 0.01 && imgGreen.complete) {{ ctx.globalAlpha = aGreen; ctx.drawImage(imgGreen, 0, 0); }}
        if (aAcc > 0.01 && imgAccents.complete) {{ ctx.globalAlpha = aAcc; ctx.drawImage(imgAccents, 0, 0); }}
        ctx.restore();
      }}

      // Evaluate spinning epicycles at current phase
      const phase = (simTime / 6.5333) % 1.0;
      const twoPiT = 2 * Math.PI * phase;
      let curX = CX_ORIG;
      let curY = CY_ORIG;

      const joints = [[OFF_X + curX * SCALE, OFF_Y + curY * SCALE]];
      for (let i = 1; i < M; i++) {{
        const [k, re, im, amp] = COEFFS[i];
        const ang = twoPiT * k;
        const ca = Math.cos(ang), sa = Math.sin(ang);
        const prevX = OFF_X + curX * SCALE;
        const prevY = OFF_Y + curY * SCALE;
        curX += re * ca - im * sa;
        curY += re * sa + im * ca;
        const nextX = OFF_X + curX * SCALE;
        const nextY = OFF_Y + curY * SCALE;
        joints.push([nextX, nextY]);

        if (i < 180 && amp * SCALE > 1.2) {{
          ctx.strokeStyle = `rgba(115, 210, 255, ${{Math.min(0.45, 0.12 + 1.5 / (i + 3))}})`;
          ctx.lineWidth = i < 12 ? 1.5 : 1.0;
          ctx.beginPath();
          ctx.arc(prevX, prevY, amp * SCALE, 0, 2 * Math.PI);
          ctx.stroke();
        }}
      }}

      // Radius vector chain
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)';
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(joints[0][0], joints[0][1]);
      for (let i = 1; i < Math.min(joints.length, 250); i++) {{
        ctx.lineTo(joints[i][0], joints[i][1]);
      }}
      ctx.stroke();

      const tip = joints[joints.length - 1];
      trail.push([tip[0], tip[1]]);
      if (trail.length > 650) trail.shift();

      // Draw glowing trace
      if (trail.length > 2) {{
        ctx.strokeStyle = 'rgba(240, 252, 255, 0.92)';
        ctx.lineWidth = 2.2;
        ctx.beginPath();
        ctx.moveTo(trail[0][0], trail[0][1]);
        for (let i = 1; i < trail.length; i++) {{
          ctx.lineTo(trail[i][0], trail[i][1]);
        }}
        ctx.stroke();
      }}

      // HUD Box
      ctx.fillStyle = 'rgba(10, 14, 24, 0.84)';
      ctx.fillRect(36, 32, 465, 145);
      ctx.strokeStyle = '#4285F4';
      ctx.strokeRect(36, 32, 465, 145);

      ctx.fillStyle = '#8ab4f8';
      ctx.font = 'bold 14px monospace';
      ctx.fillText('GEMINI // FOURIER EPICYCLE ENGINE', 54, 58);
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 32px monospace';
      ctx.fillText(`CIRCLES: ${{M.toLocaleString()}} / 2,049`, 54, 100);
      ctx.fillStyle = errPct < 1.5 ? '#34A853' : '#FBBC05';
      ctx.font = 'bold 20px monospace';
      ctx.fillText(`APPROX ERROR: ${{errPct.toFixed(2)}}%`, 54, 134);
      ctx.fillStyle = '#9aa0a6';
      ctx.font = '13px monospace';
      ctx.fillText('z_M(t) = Σ c_k exp(i·2π·k·t)  [k ∈ -1024..+1024]', 54, 160);

      requestAnimationFrame(render);
    }}
    requestAnimationFrame(render);
  </script>
</body>
</html>
"""

with open("interactive/index.html", "w") as f:
    f.write(html_content)
print("Wrote interactive/index.html")
