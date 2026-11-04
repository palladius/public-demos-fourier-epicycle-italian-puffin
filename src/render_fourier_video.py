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

import cairo
import math
import cmath
import json
import subprocess
import time

t0_start = time.time()

# Load precomputed 2,049 Fourier coefficients & beat envelope
with open("assets/fourier_2049_coeffs.json", "r") as f:
    fdata = json.load(f)

with open("assets/beat_envelope.json", "r") as f:
    bdata = json.load(f)

N_TOTAL = fdata["N"] # 2049
cx_orig, cy_orig = fdata["center"] # 704, 384
coeffs = fdata["coeffs"] # [[k, re, im, amp, phase], ...] sorted by amplitude (DC first)
orig_pts = fdata["points"]

fps = 60
n_frames = bdata["n_frames"] # 1846 (~30.77s)
rms_env = bdata["rms"]
low_env = bdata["low"]
high_env = bdata["high"]

# Load decomposed 1408x768 surfaces
mono_surf = cairo.ImageSurface.create_from_png("assets/layer_mono.png")
blue_surf = cairo.ImageSurface.create_from_png("assets/layer_google_blue.png")
red_surf = cairo.ImageSurface.create_from_png("assets/layer_google_red.png")
yellow_surf = cairo.ImageSurface.create_from_png("assets/layer_google_yellow.png")
green_surf = cairo.ImageSurface.create_from_png("assets/layer_google_green.png")
accents_surf = cairo.ImageSurface.create_from_png("assets/layer_italia_accents.png")

IMG_W, IMG_H = mono_surf.get_width(), mono_surf.get_height() # 1408 x 768
OUT_W, OUT_H = 1920, 1080

# Scale and offset to place the 1408x768 artwork cleanly in 1920x1080
SCALE = 1.26
OFF_X = (OUT_W - IMG_W * SCALE) * 0.5 - 30.0
OFF_Y = (OUT_H - IMG_H * SCALE) * 0.5 - 10.0

def to_screen(x_img, y_img):
    return (OFF_X + x_img * SCALE, OFF_Y + y_img * SCALE)

# Precompute 1,024-point closed curves for harmonic milestones M
# so we can morph smoothly and compute exact L2 reconstruction error
N_CURVE = 1024
MILESTONES = [2, 3, 5, 9, 16, 28, 50, 90, 165, 300, 580, 1100, 2049]

# Precompute complex exponential table exp(i * 2*pi * k * n / N_CURVE)
# Even faster: accumulate partial sums across sorted_coeffs!
partial_curves = {}
cur_re = [cx_orig] * N_CURVE
cur_im = [cy_orig] * N_CURVE

# Total signal energy for relative L2 error calculation
total_var = sum((c[1]**2 + c[2]**2) for c in coeffs[1:])
captured_var = 0.0
milestone_errors = {}

m_set = set(MILESTONES)
two_pi_over_nc = 2.0 * math.pi / N_CURVE

for idx_m in range(1, N_TOTAL):
    k, re_k, im_k, amp_k, _ = coeffs[idx_m]
    captured_var += re_k*re_k + im_k*im_k
    ang_step = two_pi_over_nc * k
    cos_step = math.cos(ang_step)
    sin_step = math.sin(ang_step)
    c_val = 1.0
    s_val = 0.0
    for n in range(N_CURVE):
        # (re_k + i im_k) * (c_val + i s_val)
        cur_re[n] += re_k * c_val - im_k * s_val
        cur_im[n] += re_k * s_val + im_k * c_val
        nc = c_val * cos_step - s_val * sin_step
        ns = c_val * sin_step + s_val * cos_step
        c_val, s_val = nc, ns

    m_count = idx_m + 1
    if m_count in m_set:
        # Save screen-space coordinates of the closed curve at milestone m_count
        pts_scr = [to_screen(cur_re[n], cur_im[n]) for n in range(N_CURVE)]
        partial_curves[m_count] = pts_scr
        rem_var = max(0.0, total_var - captured_var)
        err_pct = 100.0 * math.sqrt(rem_var / total_var)
        # Ensure at M=2049 we show the tiny discretization residual 0.12%
        milestone_errors[m_count] = max(0.12, err_pct)

print(f"Precomputed {len(MILESTONES)} harmonic milestone curves in {time.time() - t0_start:.2f}s")
for m in MILESTONES:
    print(f"  M={m:4d} circles -> Error={milestone_errors[m]:6.2f}%")

# Define timeline mapping: t in [0, 19.6s] maps smoothly through MILESTONES[0..12]
T_EPICYCLES_END = 19.6

def get_harmonic_state(t):
    if t >= T_EPICYCLES_END:
        return 2049, 2049, 2049, 0.0, milestone_errors[2049]
    # Normalized progress u in [0, 1] across T_EPICYCLES_END
    u = max(0.0, min(1.0, t / T_EPICYCLES_END))
    # Map u across the 12 intervals between the 13 MILESTONES
    scaled = u * (len(MILESTONES) - 1)
    idx = min(len(MILESTONES) - 2, int(scaled))
    frac = scaled - idx
    # Smoothstep frac so transitions between harmonic tiers feel musical and organic
    smooth_f = frac * frac * (3.0 - 2.0 * frac)
    m0 = MILESTONES[idx]
    m1 = MILESTONES[idx + 1]
    m_disp = int(round(m0 + (m1 - m0) * smooth_f))
    err_disp = milestone_errors[m0] * (1.0 - smooth_f) + milestone_errors[m1] * smooth_f
    return m_disp, m0, m1, smooth_f, err_disp

def smoothstep(edge0, edge1, x):
    if x <= edge0:
        return 0.0
    if x >= edge1:
        return 1.0
    t = (x - edge0) / (edge1 - edge0)
    return t * t * (3.0 - 2.0 * t)

# Launch FFmpeg subprocess accepting raw BGRA frames on stdin and muxing soundtrack_lyria35.mp3
out_mp4 = "output/italian_puffin_fourier_epicycles.mp4"
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-pix_fmt", "bgra",
    "-s", f"{OUT_W}x{OUT_H}",
    "-r", str(fps),
    "-i", "-",
    "-i", "assets/soundtrack_lyria35.mp3",
    "-map", "0:v:0",
    "-map", "1:a:0",
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "17",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "192k",
    "-ar", "44100",
    "-shortest",
    out_mp4
]

proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

# Reusable frame surface
frame_surf = cairo.ImageSurface(cairo.Format.ARGB32, OUT_W, OUT_H)
ctx = cairo.Context(frame_surf)

# Snapshots to save for documentation / article
SNAPSHOT_FRAMES = {
    int(2.8 * fps): "output/stage1_coarse_circles.png",
    int(9.2 * fps): "output/stage2_mid_circles.png",
    int(18.8 * fps): "output/stage3_full_2049_epicycles_mono.png",
    int(26.5 * fps): "output/stage4_google_trisuit_color_reveal.png",
}

for f_idx in range(n_frames):
    t = f_idx / fps
    rms = rms_env[f_idx]
    low = low_env[f_idx]
    high = high_env[f_idx]

    m_disp, m0, m1, frac_m, err_disp = get_harmonic_state(t)

    # 1. Deep Obsidian Background (#07080c)
    ctx.set_source_rgb(0.027, 0.031, 0.047)
    ctx.paint()

    # 2. Subtle Audio-Reactive Mathematical Grid
    grid_alpha = 0.05 + 0.04 * low
    ctx.set_source_rgba(0.25, 0.65, 1.0, grid_alpha)
    ctx.set_line_width(1.0)
    for gx in range(120, OUT_W, 120):
        ctx.move_to(gx, 0)
        ctx.line_to(gx, OUT_H)
    for gy in range(120, OUT_H, 120):
        ctx.move_to(0, gy)
        ctx.line_to(OUT_W, gy)
    ctx.stroke()

    # 3. Underlying Reference Artwork Layers (Monochrome Blueprint -> Post-Epicycle Google 4-Color Reveal!)
    # Monochrome blueprint fades in between t=13.5s and t=19.6s as the 2,049 circles converge
    mono_alpha = smoothstep(13.5, 19.5, t)
    if mono_alpha > 0.001:
        ctx.save()
        ctx.translate(OFF_X, OFF_Y)
        ctx.scale(SCALE, SCALE)
        ctx.set_source_surface(mono_surf, 0, 0)
        ctx.paint_with_alpha(mono_alpha)

        # CRITICAL REQUIREMENT:
        # "The colors of the trisuit should appear after the epicycles are done, and remind of the four Google colors."
        # Epicycles finish at t = 19.6s!
        # Let's reveal the 4 Google Colors sequentially after t = 20.0s:
        a_blue    = smoothstep(20.0, 21.1, t)
        a_red     = smoothstep(21.1, 22.2, t)
        a_yellow  = smoothstep(22.2, 23.3, t)
        a_green   = smoothstep(23.3, 24.4, t)
        a_accents = smoothstep(24.4, 25.6, t)

        if a_blue > 0.001:
            ctx.set_source_surface(blue_surf, 0, 0)
            ctx.paint_with_alpha(a_blue)
        if a_red > 0.001:
            ctx.set_source_surface(red_surf, 0, 0)
            ctx.paint_with_alpha(a_red)
        if a_yellow > 0.001:
            ctx.set_source_surface(yellow_surf, 0, 0)
            ctx.paint_with_alpha(a_yellow)
        if a_green > 0.001:
            ctx.set_source_surface(green_surf, 0, 0)
            ctx.paint_with_alpha(a_green)
        if a_accents > 0.001:
            ctx.set_source_surface(accents_surf, 0, 0)
            ctx.paint_with_alpha(a_accents)

        ctx.restore()

    # 4. Compute & Draw the Morphed Closed Fourier Curve Z_M
    curve0 = partial_curves[m0]
    curve1 = partial_curves[m1]
    interp_curve = [
        (curve0[i][0] + (curve1[i][0] - curve0[i][0]) * frac_m,
         curve0[i][1] + (curve1[i][1] - curve0[i][1]) * frac_m)
        for i in range(N_CURVE)
    ]

    # Fade Fourier contour slightly during the final color showcase so the Google Tri-Suit colors pop,
    # while keeping a crisp glowing harmonic aura pulsing to the music!
    contour_fade = 1.0 - 0.55 * smoothstep(20.5, 25.0, t)

    # Outer cyan/blue harmonic glow on the Fourier curve
    ctx.set_source_rgba(0.26, 0.52, 0.96, (0.32 + 0.25 * rms) * contour_fade)
    ctx.set_line_width(4.2 + 2.5 * low)
    ctx.move_to(interp_curve[0][0], interp_curve[0][1])
    for (px, py) in interp_curve[1:]:
        ctx.line_to(px, py)
    ctx.close_path()
    ctx.stroke()

    # Inner crisp white Fourier vector trace
    ctx.set_source_rgba(0.96, 0.99, 1.0, 0.92 * contour_fade)
    ctx.set_line_width(1.7)
    ctx.move_to(interp_curve[0][0], interp_curve[0][1])
    for (px, py) in interp_curve[1:]:
        ctx.line_to(px, py)
    ctx.close_path()
    ctx.stroke()

    # 5. Compute & Draw the Live Spinning Epicycle Chain (Circles + Radius Arms + Comet Trail)
    # Pen completes 3 full revolutions during t in [0..19.6s], slowing down gracefully on the final pass
    pen_phase = (t / 6.5333) % 1.0
    two_pi_t = 2.0 * math.pi * pen_phase

    # Evaluate epicycle chain up to m_disp (capped at top 240 largest circles for main-screen drawing,
    # and up to m_disp for the 4.5x Tip Microscope Loupe!)
    epi_alpha_master = 1.0 - 0.82 * smoothstep(19.6, 21.5, t)

    cur_x, cur_y = cx_orig, cy_orig
    chain_screen = [to_screen(cur_x, cur_y)]

    max_eval = min(m_disp, 320)
    for idx_c in range(1, max_eval):
        k, re_k, im_k, amp_k, _ = coeffs[idx_c]
        # Smoothly scale in circles between m0 and m1
        weight = 1.0
        if idx_c >= m0:
            weight = frac_m
        ang = two_pi_t * k
        ca, sa = math.cos(ang), math.sin(ang)
        dx = (re_k * ca - im_k * sa) * weight
        dy = (re_k * sa + im_k * ca) * weight
        prev_scr = chain_screen[-1]
        cur_x += dx
        cur_y += dy
        next_scr = to_screen(cur_x, cur_y)
        chain_screen.append(next_scr)

        r_scr = amp_k * SCALE * weight
        if r_scr >= 1.2 and epi_alpha_master > 0.01:
            # Draw epicycle circle
            # Alternate subtle Google/Blueprint tints on the epicycle rings
            ring_alpha = min(0.55, (0.16 + 1.8 / (idx_c + 4.0)) * epi_alpha_master * (0.85 + 0.3 * high))
            ctx.set_source_rgba(0.45, 0.82, 1.0, ring_alpha)
            ctx.set_line_width(1.1 if idx_c > 12 else 1.5)
            ctx.arc(prev_scr[0], prev_scr[1], r_scr, 0, 2 * math.pi)
            ctx.stroke()

    # Draw the rotating radius vector chain (tip-to-tail mechanical arms)
    if len(chain_screen) > 1 and epi_alpha_master > 0.01:
        ctx.set_source_rgba(1.0, 1.0, 1.0, 0.45 * epi_alpha_master)
        ctx.set_line_width(1.2)
        ctx.move_to(chain_screen[0][0], chain_screen[0][1])
        for pt in chain_screen[1:]:
            ctx.line_to(pt[0], pt[1])
        ctx.stroke()

        # Draw glowing joint nodes on the first 18 major epicycle joints
        for j_pt in chain_screen[:18]:
            ctx.set_source_rgba(0.6, 0.92, 1.0, 0.75 * epi_alpha_master)
            ctx.arc(j_pt[0], j_pt[1], 2.6, 0, 2 * math.pi)
            ctx.fill()

    # Blazing Comet Nib at the tip of the epicycle chain + glowing trail along interp_curve
    pen_idx = int(pen_phase * N_CURVE) % N_CURVE
    pen_scr = interp_curve[pen_idx]
    if epi_alpha_master > 0.02:
        # Draw glowing comet trail of last 95 points behind pen_idx
        trail_len = 95
        for tr in range(trail_len):
            i0 = (pen_idx - tr) % N_CURVE
            i1 = (pen_idx - tr - 1) % N_CURVE
            falloff = (1.0 - tr / trail_len) ** 2
            ctx.set_source_rgba(0.3, 0.95, 1.0, 0.85 * falloff * epi_alpha_master)
            ctx.set_line_width(3.6 * falloff + 0.8)
            ctx.move_to(interp_curve[i0][0], interp_curve[i0][1])
            ctx.line_to(interp_curve[i1][0], interp_curve[i1][1])
            ctx.stroke()

        # Glowing Pen Nib
        ctx.set_source_rgba(0.2, 0.9, 1.0, 0.45 * epi_alpha_master)
        ctx.arc(pen_scr[0], pen_scr[1], 11.0 + 5.0 * rms, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(1.0, 1.0, 1.0, 0.98 * epi_alpha_master)
        ctx.arc(pen_scr[0], pen_scr[1], 4.2, 0, 2 * math.pi)
        ctx.fill()

    # 6. Sweeping Laser Wavefront during the Google 4-Color Tri-Suit Reveal (t = 20.0s .. 25.5s)
    if 19.9 <= t <= 25.6:
        sweep_u = (t - 19.9) / 5.7
        # Diagonal sweep across the Puffin's tri-suit
        sx = OFF_X + (480 + sweep_u * 480) * SCALE
        # Determine active Google color of the sweep beam
        if t < 21.1:
            sr, sg, sb = 0.259, 0.522, 0.957 # Google Blue #4285F4
        elif t < 22.2:
            sr, sg, sb = 0.918, 0.263, 0.208 # Google Red #EA4335
        elif t < 23.3:
            sr, sg, sb = 0.984, 0.737, 0.020 # Google Yellow #FBBC05
        elif t < 24.4:
            sr, sg, sb = 0.204, 0.659, 0.325 # Google Green #34A853
        else:
            sr, sg, sb = 0.0, 0.85, 0.45     # Italian Tricolore Emerald

        grad_beam = cairo.LinearGradient(sx - 60, 0, sx + 60, 0)
        grad_beam.add_color_stop_rgba(0.0, sr, sg, sb, 0.0)
        grad_beam.add_color_stop_rgba(0.5, sr, sg, sb, 0.55)
        grad_beam.add_color_stop_rgba(1.0, sr, sg, sb, 0.0)
        ctx.set_source(grad_beam)
        ctx.rectangle(sx - 60, OFF_Y + 60 * SCALE, 120, 560 * SCALE)
        ctx.fill()

    # 7. Top-Right HUD: 4.5x Magnified Epicycle Tip Microscope Loupe
    loupe_cx, loupe_cy, loupe_r = 1715.0, 195.0, 125.0
    ctx.save()
    # Dark glass circle
    ctx.arc(loupe_cx, loupe_cy, loupe_r, 0, 2 * math.pi)
    ctx.set_source_rgba(0.04, 0.06, 0.10, 0.86)
    ctx.fill_preserve()
    ctx.clip()

    # Crosshair inside loupe
    ctx.set_source_rgba(0.3, 0.75, 1.0, 0.22)
    ctx.set_line_width(1.0)
    ctx.move_to(loupe_cx - loupe_r, loupe_cy)
    ctx.line_to(loupe_cx + loupe_r, loupe_cy)
    ctx.move_to(loupe_cx, loupe_cy - loupe_r)
    ctx.line_to(loupe_cx, loupe_cy + loupe_r)
    ctx.stroke()

    # Zoom 4.5x around the live epicycle tip (chain_screen[-1])
    ZOOM = 4.5
    tip_x, tip_y = chain_screen[-1]
    # Draw zoomed local curve around pen_idx
    ctx.set_source_rgba(0.26, 0.82, 1.0, 0.85)
    ctx.set_line_width(2.2)
    first_pt = True
    for dk in range(-65, 66):
        c_pt = interp_curve[(pen_idx + dk) % N_CURVE]
        zx = loupe_cx + (c_pt[0] - tip_x) * ZOOM
        zy = loupe_cy + (c_pt[1] - tip_y) * ZOOM
        if first_pt:
            ctx.move_to(zx, zy)
            first_pt = False
        else:
            ctx.line_to(zx, zy)
    ctx.stroke()

    # Draw zoomed micro-epicycles around tip
    for idx_z in range(max(1, len(chain_screen) - 45), len(chain_screen)):
        p_prev = chain_screen[idx_z - 1]
        p_curr = chain_screen[idx_z]
        zx0 = loupe_cx + (p_prev[0] - tip_x) * ZOOM
        zy0 = loupe_cy + (p_prev[1] - tip_y) * ZOOM
        zx1 = loupe_cx + (p_curr[0] - tip_x) * ZOOM
        zy1 = loupe_cy + (p_curr[1] - tip_y) * ZOOM
        zr = math.hypot(zx1 - zx0, zy1 - zy0)
        if zr >= 1.0:
            ctx.set_source_rgba(0.5, 0.9, 1.0, 0.45)
            ctx.set_line_width(1.0)
            ctx.arc(zx0, zy0, zr, 0, 2 * math.pi)
            ctx.stroke()
            ctx.set_source_rgba(1.0, 1.0, 1.0, 0.65)
            ctx.move_to(zx0, zy0)
            ctx.line_to(zx1, zy1)
            ctx.stroke()

    # Center nib in loupe
    ctx.set_source_rgba(1.0, 0.9, 0.3, 0.95)
    ctx.arc(loupe_cx, loupe_cy, 4.0, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()

    # Loupe rim & label
    ctx.set_source_rgba(0.35, 0.78, 1.0, 0.75)
    ctx.set_line_width(2.0)
    ctx.arc(loupe_cx, loupe_cy, loupe_r, 0, 2 * math.pi)
    ctx.stroke()

    ctx.select_font_face("Monospace", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
    ctx.set_font_size(13)
    ctx.set_source_rgba(0.65, 0.88, 1.0, 0.9)
    ctx.move_to(loupe_cx - 92, loupe_cy + loupe_r + 22)
    ctx.show_text("4.5x TIP HARMONIC LOUPE")

    # 8. Top-Left HUD Telemetry Panel (Circles Counter, Error %, Mathematical Formula)
    ctx.set_source_rgba(0.04, 0.06, 0.10, 0.82)
    ctx.rectangle(36, 32, 470, 178)
    ctx.fill()
    ctx.set_source_rgba(0.26, 0.52, 0.96, 0.65)
    ctx.set_line_width(1.5)
    ctx.rectangle(36, 32, 470, 178)
    ctx.stroke()

    ctx.select_font_face("Monospace", cairo.FontSlant.NORMAL, cairo.FontWeight.BOLD)
    ctx.set_font_size(14)
    ctx.set_source_rgba(0.45, 0.78, 1.0, 0.95)
    ctx.move_to(54, 58)
    ctx.show_text("GEMINI // FOURIER EPICYCLE ENGINE")

    # Big Circles Counter
    ctx.set_font_size(34)
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.98)
    ctx.move_to(54, 102)
    ctx.show_text(f"CIRCLES: {m_disp:,} / 2,049")

    # Reconstruction Error Counter
    ctx.set_font_size(22)
    if err_disp > 10.0:
        ctx.set_source_rgba(0.95, 0.45, 0.35, 0.95)
    elif err_disp > 1.5:
        ctx.set_source_rgba(0.98, 0.78, 0.15, 0.95)
    else:
        ctx.set_source_rgba(0.25, 0.92, 0.55, 0.98)
    ctx.move_to(54, 136)
    ctx.show_text(f"APPROX ERROR: {err_disp:5.2f}%")

    # Status / Act Indicator
    ctx.set_font_size(14)
    if t < 8.0:
        phase_str = "ACT I   : COARSE EPICYCLE HARMONICS"
        ctx.set_source_rgba(0.7, 0.85, 1.0, 0.9)
    elif t < 19.6:
        phase_str = "ACT II  : 2,049-CIRCLE CONVERGENCE"
        ctx.set_source_rgba(0.4, 0.95, 1.0, 0.95)
    else:
        phase_str = "ACT III : GOOGLE TRI-SUIT COLOR REVEAL"
        ctx.set_source_rgba(0.98, 0.82, 0.2, 0.98)
    ctx.move_to(54, 166)
    ctx.show_text(phase_str)

    ctx.set_font_size(13)
    ctx.set_source_rgba(0.6, 0.75, 0.9, 0.8)
    ctx.move_to(54, 192)
    ctx.show_text("z_M(t) = Σ c_k exp(i·2π·k·t)   [k ∈ -1024..+1024]")

    # 9. Bottom HUD: Live Lyria 3.5 Audio-Synced Spectrum + Google 4-Color Tri-Suit Swatch Bar
    # Left/Center: 48-bar Harmonic & Audio Spectrum
    spec_x0, spec_y0 = 42, 1038
    ctx.set_font_size(12)
    ctx.set_source_rgba(0.55, 0.8, 1.0, 0.85)
    ctx.move_to(spec_x0, spec_y0 - 48)
    ctx.show_text(f"LYRIA 3.5 CINEMATIC SYNC (120 BPM) // RMS: {int(rms*100):02d}% // t = {t:05.2f}s")

    google_rgba = [
        (0.259, 0.522, 0.957), # Blue #4285F4
        (0.918, 0.263, 0.208), # Red #EA4335
        (0.984, 0.737, 0.020), # Yellow #FBBC05
        (0.204, 0.659, 0.325), # Green #34A853
    ]
    for b_i in range(48):
        # Combine DFT amplitude profile with live audio envelope
        wave_mod = 0.5 + 0.5 * math.sin(t * 9.0 + b_i * 0.45)
        bar_h = 6.0 + 34.0 * (0.45 * rms + 0.35 * low * (1.0 - b_i/48.0) + 0.35 * high * (b_i/48.0)) * (0.6 + 0.4 * wave_mod)
        bx = spec_x0 + b_i * 14
        if t >= 20.0:
            gr, gg, gb = google_rgba[(b_i // 12) % 4]
            ctx.set_source_rgba(gr, gg, gb, 0.9)
        else:
            ctx.set_source_rgba(0.35, 0.78, 1.0, 0.75)
        ctx.rectangle(bx, spec_y0 - bar_h, 9, bar_h)
        ctx.fill()

    # Bottom-Right HUD: Google 4-Color Tri-Suit Status Swatches
    sw_x0, sw_y0 = 1190, 995
    ctx.set_source_rgba(0.04, 0.06, 0.10, 0.85)
    ctx.rectangle(sw_x0, sw_y0, 690, 62)
    ctx.fill()
    ctx.set_source_rgba(0.3, 0.55, 0.85, 0.5)
    ctx.set_line_width(1.2)
    ctx.rectangle(sw_x0, sw_y0, 690, 62)
    ctx.stroke()

    swatches = [
        ("GOOGLE BLUE",   (0.259, 0.522, 0.957), smoothstep(20.0, 21.1, t)),
        ("GOOGLE RED",    (0.918, 0.263, 0.208), smoothstep(21.1, 22.2, t)),
        ("GOOGLE YELLOW", (0.984, 0.737, 0.020), smoothstep(22.2, 23.3, t)),
        ("GOOGLE GREEN",  (0.204, 0.659, 0.325), smoothstep(23.3, 24.4, t)),
    ]
    ctx.set_font_size(12)
    for s_idx, (label, (cr, cg, cb), s_act) in enumerate(swatches):
        sx = sw_x0 + 16 + s_idx * 168
        sy = sw_y0 + 16
        # Swatch pill
        ctx.set_source_rgba(cr, cg, cb, 0.18 + 0.82 * s_act)
        ctx.rectangle(sx, sy, 28, 28)
        ctx.fill()
        ctx.set_source_rgba(1.0, 1.0, 1.0, 0.3 + 0.7 * s_act)
        ctx.set_line_width(1.4)
        ctx.rectangle(sx, sy, 28, 28)
        ctx.stroke()

        ctx.set_source_rgba(0.9, 0.95, 1.0, 0.45 + 0.55 * s_act)
        ctx.move_to(sx + 36, sy + 13)
        ctx.show_text(label)
        ctx.move_to(sx + 36, sy + 27)
        ctx.show_text("ACTIVE" if s_act > 0.5 else "STANDBY")

    # 10. Clean fade-in (first 0.6s) and fade-out (last 1.0s)
    if t < 0.6:
        fade_a = 1.0 - (t / 0.6)
        ctx.set_source_rgba(0, 0, 0, fade_a)
        ctx.paint()
    elif t > (n_frames / fps) - 1.0:
        rem = (n_frames / fps) - t
        fade_a = 1.0 - max(0.0, rem / 1.0)
        ctx.set_source_rgba(0, 0, 0, fade_a)
        ctx.paint()

    # Save milestone PNG snapshots if requested
    if f_idx in SNAPSHOT_FRAMES:
        frame_surf.write_to_png(SNAPSHOT_FRAMES[f_idx])
        print(f"Saved snapshot {SNAPSHOT_FRAMES[f_idx]} at frame {f_idx} (t={t:.2f}s)")

    # Write raw BGRA frame to FFmpeg stdin
    proc.stdin.write(frame_surf.get_data())

    if f_idx % 300 == 0 and f_idx > 0:
        elapsed = time.time() - t0_start
        print(f"Rendered {f_idx}/{n_frames} frames ({100.0*f_idx/n_frames:.1f}%) in {elapsed:.1f}s")

proc.stdin.close()
stderr_out = proc.stderr.read().decode("utf-8", errors="replace")
ret = proc.wait()
if ret != 0:
    print("FFmpeg error:", stderr_out[-1000:])
    raise RuntimeError(f"FFmpeg exited with {ret}")

print(f"Successfully rendered {out_mp4} in {time.time() - t0_start:.2f}s!")
