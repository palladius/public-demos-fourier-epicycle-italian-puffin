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

import math
import cmath
import json
import cairo

def interp_poly(pts, step=2.5):
    out = []
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        dist = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(dist / step))
        for k in range(n):
            t = k / n
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    out.append(pts[-1])
    return out

def arc_pts(cx, cy, r, a0_deg, a1_deg, step_deg=3.0):
    out = []
    diff = a1_deg - a0_deg
    n = max(2, int(abs(diff) / step_deg))
    for k in range(n + 1):
        a = math.radians(a0_deg + diff * (k / n))
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out

def cubic_bezier(p0, p1, p2, p3, n=32):
    out = []
    for k in range(n + 1):
        t = k / n
        mt = 1.0 - t
        x = (mt**3)*p0[0] + 3*(mt**2)*t*p1[0] + 3*mt*(t**2)*p2[0] + (t**3)*p3[0]
        y = (mt**3)*p0[1] + 3*(mt**2)*t*p1[1] + 3*mt*(t**2)*p2[1] + (t**3)*p3[1]
        out.append((x, y))
    return out

def build_clean_puffin_contour():
    path = []
    rear_cx, rear_cy = 482.0, 560.0
    front_cx, front_cy = 902.0, 560.0
    bb_x, bb_y = 668.0, 576.0

    # 1. Rear wheel: hub -> outer tire (360 deg) -> inner rim (360 deg) -> 8 spokes -> hub
    r_top_x = rear_cx + 142.0 * math.cos(math.radians(-50))
    r_top_y = rear_cy + 142.0 * math.sin(math.radians(-50))
    path += interp_poly([(rear_cx, rear_cy), (r_top_x, r_top_y)])
    path += arc_pts(rear_cx, rear_cy, 142.0, -50.0, 310.0, 3.0)
    path += arc_pts(rear_cx, rear_cy, 123.0, 310.0, -50.0, 3.5)
    for sp_ang in range(-50, 310, 45):
        rad = math.radians(sp_ang)
        rx, ry = rear_cx + 123.0 * math.cos(rad), rear_cy + 123.0 * math.sin(rad)
        path += interp_poly([(rear_cx, rear_cy), (rx, ry), (rear_cx, rear_cy)], step=5.0)

    # 2. Seatstay up to Seat Cluster (598, 412) -> Seatpost -> Saddle -> Puffin Tail Feathers
    path += interp_poly([
        (rear_cx, rear_cy),
        (598, 412),
        (576, 342),
        (525, 326),
        (542, 332),
        (490, 328),
        (505, 322),
        (468, 308), # Tail tip
    ])

    # 3. Puffin Aero Back Silhouette (Tail -> Hip -> Back -> Neck)
    path += cubic_bezier((468, 308), (498, 292), (522, 278), (538, 268), 24)
    path += cubic_bezier((538, 268), (568, 202), (642, 162), (752, 160), 40)

    # 4. Internal Tri-Suit 4-Google-Color Geometric Panels
    # Panel 1: Google Blue Shoulder & Sleeve
    path += cubic_bezier((752, 160), (725, 166), (702, 182), (696, 208), 20)
    path += cubic_bezier((696, 208), (722, 232), (732, 275), (740, 322), 24)
    path += interp_poly([(740, 322), (785, 315)], step=3.0)
    path += cubic_bezier((785, 315), (786, 265), (782, 215), (752, 160), 24)

    # Panel 2: Google Yellow Upper Wedge
    path += cubic_bezier((752, 160), (725, 166), (702, 182), (696, 208), 16)
    path += interp_poly([(696, 208), (622, 188), (576, 215), (618, 255), (696, 208)], step=3.5)

    # Panel 3: Google Red Core Torso & Thigh Panel
    path += interp_poly([(696, 208), (712, 228), (732, 288), (696, 298)], step=3.5)
    path += cubic_bezier((696, 298), (655, 312), (655, 345), (688, 382), 20)
    path += interp_poly([(688, 382), (662, 405)], step=3.0)
    path += cubic_bezier((662, 405), (612, 355), (578, 310), (576, 255), 24)
    path += interp_poly([(576, 255), (618, 255)], step=3.0)

    # Panel 4: Google Green Rear Hip & Shorts Panel
    path += interp_poly([(618, 255), (576, 255), (538, 268)], step=3.0)
    path += cubic_bezier((538, 268), (535, 315), (575, 375), (645, 422), 28)
    path += interp_poly([(645, 422), (662, 405)], step=3.0)
    path += cubic_bezier((662, 405), (612, 355), (578, 310), (618, 255), 20)
    path += interp_poly([(618, 255), (696, 208), (752, 160)], step=4.0)

    # 5. Italian Cycling Helmet ("ITALIA" 🇮🇹)
    path += cubic_bezier((752, 160), (748, 115), (775, 82), (818, 84), 28)
    path += cubic_bezier((818, 84), (858, 86), (882, 106), (890, 128), 24)
    path += interp_poly([
        (890, 128), (908, 152), (868, 145), (830, 136), (768, 152), (830, 136), (868, 145)
    ], step=3.0)

    # 6. Iconic Striped Puffin Beak & White Cheek & Eye
    path += cubic_bezier((868, 145), (902, 168), (918, 196), (918, 226), 24)
    path += cubic_bezier((918, 226), (892, 232), (870, 226), (854, 212), 20)
    # Beak internal stripes
    path += interp_poly([
        (854, 212), (882, 158), (898, 174), (875, 225), (894, 228), (906, 188), (918, 226), (854, 212)
    ], step=3.0)
    # White cheek & triangular Puffin eye
    path += cubic_bezier((854, 212), (822, 228), (782, 212), (775, 168), 24)
    path += interp_poly([
        (775, 168), (825, 162), (840, 152), (846, 172), (830, 174), (840, 152), (868, 145), (854, 212)
    ], step=3.0)

    # 7. Puffin Aero Arms & Drop Handlebars + Brake Levers
    path += interp_poly([(854, 212), (812, 248), (785, 315)], step=4.0)
    path += cubic_bezier((785, 315), (822, 342), (865, 352), (906, 364), 24)
    path += interp_poly([(906, 364), (912, 412), (904, 378), (884, 385)], step=3.0)
    path += cubic_bezier((884, 385), (898, 415), (890, 448), (850, 452), 22)
    path += cubic_bezier((850, 452), (875, 440), (875, 405), (848, 382), 18)
    path += interp_poly([(848, 382), (808, 395), (752, 352), (740, 322), (752, 352), (808, 395)], step=4.0)

    # 8. Head Tube & Front Fork down to Front Wheel (902, 560)
    path += interp_poly([(808, 395), (822, 435), (front_cx, front_cy)], step=4.0)
    f_top_x = front_cx + 142.0 * math.cos(math.radians(-120))
    f_top_y = front_cy + 142.0 * math.sin(math.radians(-120))
    path += interp_poly([(front_cx, front_cy), (f_top_x, f_top_y)])
    path += arc_pts(front_cx, front_cy, 142.0, -120.0, 240.0, 3.0)
    path += arc_pts(front_cx, front_cy, 123.0, 240.0, -120.0, 3.5)
    for sp_ang in range(-120, 240, 45):
        rad = math.radians(sp_ang)
        rx, ry = front_cx + 123.0 * math.cos(rad), front_cy + 123.0 * math.sin(rad)
        path += interp_poly([(front_cx, front_cy), (rx, ry), (front_cx, front_cy)], step=5.0)

    # 9. Front Hub up Fork -> Top Tube -> Seat Tube -> Down Tube -> Bottom Bracket (668, 576)
    path += interp_poly([
        (front_cx, front_cy),
        (822, 435),
        (808, 395),
        (598, 412), # Top tube
        (bb_x, bb_y), # Seat tube
        (822, 435), # Down tube
        (bb_x, bb_y),
    ], step=4.0)

    # 10. Crankset & Pedaling Legs + Cycling Shoes
    path += arc_pts(bb_x, bb_y, 38.0, 0.0, 360.0, 8.0)
    path += interp_poly([
        (bb_x, bb_y),
        (692, 542),
        (732, 558), # Red cycling shoe toe
        (662, 538),
        (645, 512), # Shoe heel
        (698, 412), # Front knee
        (645, 422), # Thigh cuff
        (582, 522), # Back leg shin
        (558, 518), # Rear shoe
        (580, 555),
        (bb_x, bb_y),
    ], step=3.5)

    # 11. Chainstay back to Rear Hub (482, 560) to close the loop seamlessly!
    path += interp_poly([
        (bb_x, bb_y),
        (482, 592),
        (rear_cx, rear_cy)
    ], step=3.5)

    return path

def resample_uniform(pts, N=2049):
    dists = [0.0]
    for i in range(1, len(pts)):
        d = math.hypot(pts[i][0] - pts[i-1][0], pts[i][1] - pts[i-1][1])
        dists.append(dists[-1] + d)
    total_len = dists[-1]
    out = []
    idx = 0
    for k in range(N):
        target = (k / N) * total_len
        while idx < len(dists) - 2 and dists[idx + 1] < target:
            idx += 1
        d0, d1 = dists[idx], dists[idx + 1]
        t = (target - d0) / max(1e-9, d1 - d0)
        x = pts[idx][0] + (pts[idx + 1][0] - pts[idx][0]) * t
        y = pts[idx][1] + (pts[idx + 1][1] - pts[idx][1]) * t
        out.append((x, y))
    return out

raw_pts = build_clean_puffin_contour()
N = 2049
pts_2049 = resample_uniform(raw_pts, N)

# Use the exact mean centroid of pts_2049 so DC term k=0 is (0, 0)!
cx0 = sum(p[0] for p in pts_2049) / N
cy0 = sum(p[1] for p in pts_2049) / N
z_samples = [complex(x - cx0, y - cy0) for (x, y) in pts_2049]

coeffs = []
two_pi_over_N = -2.0 * math.pi / N
for k in range(-1024, 1025):
    angle_step = two_pi_over_N * k
    w_step = cmath.rect(1.0, angle_step)
    w_cur = 1.0 + 0.0j
    s = 0.0 + 0.0j
    for zn in z_samples:
        s += zn * w_cur
        w_cur *= w_step
    Xk = s / N
    coeffs.append((k, Xk.real, Xk.imag, abs(Xk), math.atan2(Xk.imag, Xk.real)))

dc_term = [c for c in coeffs if c[0] == 0]
ac_terms = sorted([c for c in coeffs if c[0] != 0], key=lambda c: c[3], reverse=True)
sorted_coeffs = dc_term + ac_terms

with open("assets/fourier_2049_coeffs.json", "w") as f:
    json.dump({
        "N": N,
        "center": [round(cx0, 4), round(cy0, 4)],
        "points": [[round(x, 2), round(y, 2)] for (x, y) in pts_2049],
        "coeffs": [[k, round(re, 5), round(im, 5), round(amp, 5), round(phase, 5)] for (k, re, im, amp, phase) in sorted_coeffs]
    }, f)
print(f"Saved clean 2,049-point Fourier contour with exact centroid ({cx0:.2f}, {cy0:.2f})!")
