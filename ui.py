import os, json, time, math, random, threading
import tkinter as tk
from collections import deque
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import sys, socket
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# Configuration & Styling
# ─────────────────────────────────────────────────────────────
def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

BASE_DIR   = get_base_dir()
CONFIG_DIR = BASE_DIR / "config"
API_FILE   = CONFIG_DIR / "api_keys.json"

SYSTEM_NAME = "Malika"
MODEL_BADGE = "PROTOTYPE CORE v4.0"

# Professional Tech Palette
C_BG      = "#02080a"
C_PRI     = "#00e5ff"
C_PRI_G   = "#0088aa"
C_MID     = "#003a4d"
C_DIM     = "#001a24"
C_DIMMER  = "#000d14"
C_ACC     = "#ff8c00"
C_ACC2    = "#00ffcc"
C_TEXT    = "#c2f9ff"
C_PANEL   = "#031117"
C_BORDER  = "#005a73"

# ─────────────────────────────────────────────────────────────
# Mood colour map  (kayfiyat bo'yicha yuz rangi)
# ─────────────────────────────────────────────────────────────
MOOD_COLORS = {
    "neutral":   {"top": C_PRI,     "bot": C_PRI_G},
    "happy":     {"top": "#4caf50", "bot": "#388e3c"},
    "surprised": {"top": "#ff9800", "bot": "#e65100"},
}

# ─────────────────────────────────────────────────────────────
# JarvisUI
# ─────────────────────────────────────────────────────────────
class JarvisUI:
    def __init__(self, face_path, size=None):
        self.root = tk.Tk()
        self.root.title(f"{SYSTEM_NAME} — Advanced Neural Interface")
        self.root.resizable(False, False)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        W  = min(sw, 1024)
        H  = min(sh, 860)
        self.root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.root.configure(bg=C_BG)

        self.W, self.H = W, H
        self.FACE_SZ   = int(H * 0.70)
        self.FCX       = W // 2
        self.FCY       = int(H * 0.45)

        # ── Animation States ─────────────────────────────
        self.speaking     = False
        self.scale        = 1.0
        self.target_scale = 1.0
        self.halo_a       = 80.0
        self.target_halo  = 80.0
        self.mouth_h      = 0.0
        self.target_mouth = 0.0
        self.SPLIT_RATIO  = 0.51
        self.tick         = 0
        self.last_t       = time.time()

        # ── Jonli harakatlar (Floating & Blinking) ───────
        self.blink_state  = 0  # 0: ochiq, 1-2: yopilish, 3-5: yopiq, 6-7: ochilish
        self.floating_y   = 0.0

        # ── Mood (yangi) ──────────────────────────────────
        self.mood         = "neutral"   # neutral | happy | surprised

        # ── Rotations & Particles ─────────────────────────
        self.rotations   = [0.0] * 6
        self.particles   = [
            {"x": random.randint(0, W), "y": random.randint(0, H),
             "s": random.uniform(0.5, 2.0), "v": random.uniform(0.2, 0.8)}
            for _ in range(40)
        ]
        self.pulse_waves = []

        self.status_text   = "SYSTEM ONLINE"
        self.net_status    = "CHECKING..."
        self.vision_status = "READY"
        self.last_net_chk  = 0
        self.status_blink  = True
        self.typing_queue  = deque()
        self.is_typing     = False
        self._running      = True

        # ── Asset Loading ─────────────────────────────────
        self._face_pil       = None
        self._upper_face_pil = None
        self._jaw_pil        = None
        self._lip_mask_pil   = None
        self._has_face       = False

        self._upper_tk       = None
        self._jaw_tk         = None
        self._mask_tk        = None
        self._last_scale_key = -1

        self._load_face(face_path)
        self._prepare_mouth()

        # ── Canvas ────────────────────────────────────────
        self.canvas = tk.Canvas(self.root, width=W, height=H,
                                bg=C_BG, highlightthickness=0)
        self.canvas.place(x=0, y=0)

        # ── Stats Panel (jonli ko'rsatkichlar) ───────────────
        PW, PH = int(W * 0.92), 110
        self.stats_container = tk.Frame(
            self.root, bg=C_PANEL,
            highlightbackground=C_BORDER, highlightthickness=1)
        self.stats_container.place(
            x=(W - PW) // 2, y=H - PH - 8, width=PW, height=PH)

        self._stat_vars = {}
        stat_defs = [
            ("NET",      "CHECKING...", C_ACC2),
            ("PING",     "--- ms",      C_PRI),
            ("TEZLIK",   "0 B/s",       C_PRI),
            ("KAYFIYAT", "NEUTRAL",     C_PRI),
            ("STATUS",   "ONLINE",      C_ACC2),
        ]
        for col, (label, init_val, color) in enumerate(stat_defs):
            cell = tk.Frame(self.stats_container, bg=C_PANEL)
            cell.grid(row=0, column=col, padx=14, pady=12, sticky="nsew")
            tk.Label(cell, text=label, fg=C_PRI_G, bg=C_PANEL,
                     font=("Consolas", 8, "bold")).pack(anchor="w")
            var = tk.StringVar(value=init_val)
            lbl = tk.Label(cell, textvariable=var, fg=color, bg=C_PANEL,
                           font=("Consolas", 14, "bold"))
            lbl.pack(anchor="w")
            self._stat_vars[label] = var

        for col in range(len(stat_defs)):
            self.stats_container.columnconfigure(col, weight=1)

        # Log text — ko'rinmas, lekin write_log ishlashi uchun saqlanadi
        self.log_text = tk.Text(self.root, borderwidth=0)
        self.log_text.place(x=-9999, y=-9999)
        self.log_text.configure(state="disabled")
        self.log_text.tag_config("you", foreground="#ffffff")
        self.log_text.tag_config("ai",  foreground=C_PRI)
        self.log_text.tag_config("sys", foreground=C_PRI_G)

        self._start_time   = time.time()
        self._ping_ms      = 0
        self._net_bytes_old = 0
        self._net_speed_str = "0 B/s"
        self._update_stats()

        # ── Keyboard bindings (yangi) ─────────────────────
        self.root.bind("<space>",   lambda e: self._toggle_speaking())
        self.root.bind("<Key-1>",   lambda e: self._set_mood("neutral"))
        self.root.bind("<Key-2>",   lambda e: self._set_mood("happy"))
        self.root.bind("<Key-3>",   lambda e: self._set_mood("surprised"))

        # ── API Key ───────────────────────────────────────
        self._api_key_ready = self._api_keys_exist()
        if not self._api_key_ready:
            self._show_setup_ui()

        self._animate()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ── Mood & Speaking helpers (yangi) ──────────────────
    def _toggle_speaking(self):
        if self.speaking:
            self.stop_speaking()
            self.write_log("SYS: Jim.")
        else:
            self.start_speaking()
            self.write_log("AI: Gapirmoqdaman...")

    def _set_mood(self, mood: str):
        self.mood = mood
        self.write_log(f"SYS: Kayfiyat — {mood.upper()}")

    # ─────────────────────────────────────────────────────
    def on_close(self):
        self._running = False
        try:
            self.root.destroy()
        except:
            pass
        os._exit(0)

    def _load_face(self, path):
        try:
            sz  = self.FACE_SZ
            img = Image.open(path).convert("RGBA").resize((sz, sz), Image.LANCZOS)
            mask = Image.new("L", (sz, sz), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, sz, sz), fill=255)
            img.putalpha(mask)
            self._face_pil = img
            self._has_face = True
        except:
            self._has_face = False

    def _prepare_mouth(self):
        if not self._has_face:
            return
        sz      = self.FACE_SZ
        split_y = int(sz * self.SPLIT_RATIO)
        mask_h  = 10
        # Og'iz eni (o'rtadagi qirqiladigan qism) — yuzning 12% i
        self.MW_PX = int(sz * 0.12)
        mx0, mx1 = sz // 2 - self.MW_PX // 2, sz // 2 + self.MW_PX // 2

        self._upper_face_pil = self._face_pil.crop((0, 0, sz, split_y))
        self._lip_mask_pil   = self._face_pil.crop((mx0, split_y - mask_h, mx1, split_y))
        
        # Jawni 3 qismga bo'lamiz: Chap, O'rta (harakatlanadi), O'ng
        self._jaw_l_pil = self._face_pil.crop((0, split_y, mx0, sz))
        self._jaw_m_pil = self._face_pil.crop((mx0, split_y, mx1, sz))
        self._jaw_r_pil = self._face_pil.crop((mx1, split_y, sz, sz))

    @staticmethod
    def _color(r, g, b, a):
        f = a / 255.0
        return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"

    # ─────────────────────────────────────────────────────
    # Animation loop
    # ─────────────────────────────────────────────────────
    def _animate(self):
        if not self._running:
            return
        try:
            self.tick += 1
            now = time.time()

            # Timing
            interval = 0.05 if self.speaking else 0.4
            if now - self.last_t > interval:
                if self.speaking:
                    self.target_scale = random.uniform(1.05, 1.18)
                    self.target_halo  = random.uniform(180, 255)
                    self.target_mouth = random.uniform(5, 25)
                else:
                    self.target_scale = random.uniform(0.99, 1.01)
                    self.target_halo  = random.uniform(70, 100)
                    self.target_mouth = 0
                self.last_t = now

            # Mood overrides (yangi)
            if self.mood == "happy":
                self.target_scale = max(self.target_scale, 1.07)
                self.target_halo  = max(self.target_halo,  160.0)
            elif self.mood == "surprised":
                self.target_scale = max(self.target_scale, 1.12)
                self.target_halo  = max(self.target_halo,  200.0)

            # Smoothing
            self.scale   += (self.target_scale - self.scale)   * 0.2
            self.halo_a  += (self.target_halo  - self.halo_a)  * 0.15
            self.mouth_h += (self.target_mouth - self.mouth_h) * 0.35

            # Rotations
            speeds = [0.8, -0.5, 1.2, -0.9, 0.3, -1.5]
            if self.speaking:
                speeds = [s * 2.5 for s in speeds]
            for i in range(len(self.rotations)):
                self.rotations[i] = (self.rotations[i] + speeds[i]) % 360

            # Jonli harakatlar (Blinking & Floating)
            if self.blink_state == 0:
                if random.random() < 0.012: # Ko'z yumish ehtimoli
                    self.blink_state = 1
            else:
                self.blink_state += 1
                if self.blink_state > 7: # Animatsiya tugadi
                    self.blink_state = 0
            
            self.floating_y = 7 * math.sin(self.tick * 0.05) # Suzish effekti (biroz sekinroq va kengroq)

            # Particles
            for p in self.particles:
                p["y"] = (p["y"] + p["v"]) % self.H

            # Internet check every 10 s
            if now - self.last_net_chk > 10:
                self.last_net_chk = now
                threading.Thread(target=self._check_internet, daemon=True).start()

            self._draw()
            if self._running:
                self.root.after(16, self._animate)
        except (tk.TclError, KeyboardInterrupt):
            self._running = False

    # ─────────────────────────────────────────────────────
    # Draw
    # ─────────────────────────────────────────────────────
    def _draw(self):
        if not self._running:
            return
        try:
            c, W, H     = self.canvas, self.W, self.H
            cx, cy, sz  = self.FCX, self.FCY, self.FACE_SZ
            c.delete("all")

            # 1. Background Grid & Particles
            step = 50
            for x in range(0, W, step):
                c.create_line(x, 0, x, H, fill="#001a24", width=1)
            for y in range(0, H, step):
                c.create_line(0, y, W, y, fill="#001a24", width=1)

            for p in self.particles:
                c.create_oval(p["x"], p["y"],
                              p["x"] + p["s"], p["y"] + p["s"],
                              fill=C_MID, outline="")

            # 2. Tech UI Rings
            ring_configs = [
                (sz * 0.62, 3, [90, 45, 90, 45], 0),
                (sz * 0.58, 1, [30, 30, 30, 30, 30, 30], 1),
                (sz * 0.54, 4, [180, 180], 2),
                (sz * 0.50, 1, [10] * 12, 3),
            ]
            for r, width, dashes, rot_idx in ring_configs:
                angle     = self.rotations[rot_idx]
                alpha     = int(self.halo_a * (1.0 - rot_idx * 0.15))
                color     = self._color(0, 229, 255, alpha)
                total_gap = 360 / len(dashes)
                for i, d in enumerate(dashes):
                    start = (angle + i * total_gap) % 360
                    c.create_arc(cx - r, cy - r, cx + r, cy + r,
                                 start=start, extent=d * 0.8,
                                 outline=color, width=width, style="arc")

            # 3. Avatar Rendering
            if self._has_face:
                # ── Rasm bilan (Puppetry) ─────────────────
                cur_sz = int(sz * self.scale)
                if cur_sz > 0 and cur_sz != self._last_scale_key:
                    self._last_scale_key = cur_sz
                    u_h = max(1, int(cur_sz * self.SPLIT_RATIO))
                    j_h = max(1, cur_sz - u_h)
                    m_h = 10
                    
                    # Scaled coordinates
                    mw_c  = int(cur_sz * 0.12)
                    mx0_c = cur_sz // 2 - mw_c // 2
                    mx1_c = cur_sz // 2 + mw_c // 2

                    try:
                        self._u_tk = ImageTk.PhotoImage(
                            self._upper_face_pil.resize((cur_sz, u_h), Image.BILINEAR))
                        self._m_tk = ImageTk.PhotoImage(
                            self._lip_mask_pil.resize((mw_c, m_h), Image.BILINEAR))
                        
                        self._jl_tk = ImageTk.PhotoImage(self._jaw_l_pil.resize((mx0_c, j_h), Image.BILINEAR))
                        self._jm_tk = ImageTk.PhotoImage(self._jaw_m_pil.resize((mw_c, j_h), Image.BILINEAR))
                        self._jr_tk = ImageTk.PhotoImage(self._jaw_r_pil.resize((cur_sz - mx1_c, j_h), Image.BILINEAR))
                        
                        self._cached_uh   = u_h
                        self._cached_jh   = j_h
                        self._cached_mh   = m_h
                        self._cached_mwc  = mw_c
                        self._cached_mx0c = mx0_c
                    except:
                        pass

                jx       = random.uniform(-0.5, 0.5) if self.speaking else 0
                jy       = random.uniform(-0.5, 0.5) if self.speaking else 0
                top_y    = cy - cur_sz // 2 + jy + self.floating_y
                open_amt = int(self.mouth_h * self.scale * 0.22)

                if self.speaking:
                    mw = int(self._cached_mwc * 0.45)
                    c.create_oval(cx - mw + jx,
                                  top_y + self._cached_uh - 2,
                                  cx + mw + jx,
                                  top_y + self._cached_uh + open_amt,
                                  fill="#150000", outline="")

                if self._u_tk:
                    c.create_image(cx + jx,
                                   top_y + self._cached_uh // 2,
                                   image=self._u_tk)
                    
                    # ── Ko'z yumish (Smooth Blinking) ─────────
                    if self.blink_state > 0:
                        # Yangi avatar (Teacher_texno) uchun aniq koordinatalar
                        eye_y = top_y + int(cur_sz * 0.366)
                        eye_w = int(cur_sz * 0.046) 
                        
                        # Animatsiya fazasiga qarab ko'z balandligi
                        if self.blink_state in [1, 7]: # Yarim ochiq
                            eye_h = int(cur_sz * 0.018)
                        elif self.blink_state in [2, 6]: # Deyarli yopiq
                            eye_h = int(cur_sz * 0.008)
                        else: # To'liq yopiq (3, 4, 5)
                            eye_h = int(cur_sz * 0.003)
                        
                        lid_color = "#121212" # Cap soyasiga mos to'q rang
                        
                        # Chap ko'z
                        lx = cx - int(cur_sz * 0.096) + jx
                        c.create_oval(lx - eye_w, eye_y - eye_h,
                                      lx + eye_w, eye_y + eye_h,
                                      fill=lid_color, outline=C_PRI, width=1)
                        
                        # O'ng ko'z
                        rx = cx + int(cur_sz * 0.096) + jx
                        c.create_oval(rx - eye_w, eye_y - eye_h,
                                      rx + eye_w, eye_y + eye_h,
                                      fill=lid_color, outline=C_PRI, width=1)

                # Jag' qismlari (Chap va O'ng qismlar qimirlamaydi)
                if hasattr(self, "_jl_tk"):
                    c.create_image(cx - cur_sz // 2 + self._cached_mx0c // 2 + jx,
                                   top_y + self._cached_uh + self._cached_jh // 2,
                                   image=self._jl_tk)
                if hasattr(self, "_jr_tk"):
                    jr_w = cur_sz - (self._cached_mx0c + self._cached_mwc)
                    c.create_image(cx + cur_sz // 2 - jr_w // 2 + jx,
                                   top_y + self._cached_uh + self._cached_jh // 2,
                                   image=self._jr_tk)

                # Faqat o'rtadagi qism ochiladi
                if hasattr(self, "_jm_tk"):
                    c.create_image(cx + jx,
                                   top_y + self._cached_uh + self._cached_jh // 2 + open_amt,
                                   image=self._jm_tk)

                if self.speaking and self._m_tk:
                    c.create_image(cx + jx,
                                   top_y + self._cached_uh - self._cached_mh // 2,
                                   image=self._m_tk)
            else:
                # ── Geometrik yuz (rasm yo'q bo'lganda) ──
                self._draw_geometric_face(c, cx, cy, sz)

            # 4. Data Overlays
            scan_y = (self.tick * 4) % H
            c.create_line(0, scan_y, W, scan_y,
                          fill=self._color(0, 229, 255, 30), width=1)

            c.create_text(30, 30, text=f"SYSTEM: {SYSTEM_NAME}",
                          fill=C_PRI, font=("Consolas", 10, "bold"), anchor="nw")
            c.create_text(30, 50, text=f"CORE: {MODEL_BADGE}",
                          fill=C_MID, font=("Consolas", 8), anchor="nw")

            net_col = "#00ffcc" if "ONLINE" in self.net_status else "#ff4444"
            c.create_text(30, 70, text=f"NET: {self.net_status}",
                          fill=net_col, font=("Consolas", 9, "bold"), anchor="nw")

            vis_col = "#ff8c00" if "READY" in self.vision_status else "#00e5ff"
            c.create_text(30, 90, text=f"VISION: {self.vision_status}",
                          fill=vis_col, font=("Consolas", 9, "bold"), anchor="nw")

            # Mood indicator (yangi)
            mood_c = {"neutral": C_PRI, "happy": "#4caf50", "surprised": "#ff9800"}
            c.create_text(30, 110, text=f"MOOD: {self.mood.upper()}",
                          fill=mood_c.get(self.mood, C_PRI),
                          font=("Consolas", 9, "bold"), anchor="nw")

            # Keyboard hint (yangi)
            c.create_text(W - 30, H - 20,
                          text="SPACE: Gapirish  |  1: Oddiy  |  2: Xursand  |  3: Hayron",
                          fill=C_MID, font=("Consolas", 8), anchor="se")

            c.create_text(W - 30, 30, text=time.strftime("%H:%M:%S"),
                          fill=C_PRI, font=("Consolas", 14, "bold"), anchor="ne")

            # 5. Status & Audio Visualizer
            stat_y   = cy + sz // 2 + 50
            status_c = C_ACC if self.speaking else C_PRI
            status_t = (
                "● ANALYZING" if self.speaking
                else f"{'●' if self.tick % 40 < 20 else '○'} {self.status_text}"
            )
            c.create_text(cx, stat_y, text=status_t,
                          fill=status_c, font=("Consolas", 11, "bold"))

            vy, vh, vw, vn = stat_y + 30, 25, 10, 24
            vx0 = cx - (vn * vw) // 2
            for i in range(vn):
                bar_h = (random.randint(4, vh) if self.speaking
                         else int(4 + 3 * math.sin(self.tick * 0.1 + i * 0.4)))
                col = C_PRI if bar_h > vh * 0.7 else C_MID
                c.create_rectangle(
                    vx0 + i * vw, vy + vh - bar_h,
                    vx0 + i * vw + vw - 2, vy + vh,
                    fill=col, outline="")

        except (tk.TclError, KeyboardInterrupt):
            self._running = False

    # ── Geometrik yuz (rasm bo'lmaganda) ─────────────────
    def _draw_geometric_face(self, c, cx, cy, sz):
        """Rasm yuklanmasa — PIL bilan geometrik avatar chizadi."""
        cur_sz = int(sz * self.scale)
        if cur_sz < 4:
            return

        R       = cur_sz // 2
        mood    = MOOD_COLORS.get(self.mood, MOOD_COLORS["neutral"])
        split_y = cy - R + int(cur_sz * self.SPLIT_RATIO)

        # Yuz tasviri (PIL orqali, doira clip bilan)
        key = (cur_sz, self.mood)
        if not hasattr(self, "_geo_cache") or self._geo_cache_key != key:
            self._geo_cache_key = key
            face_img = Image.new("RGBA", (cur_sz, cur_sz), (0, 0, 0, 0))
            d = ImageDraw.Draw(face_img)
            sl = int(cur_sz * self.SPLIT_RATIO)

            def hex2rgb(h):
                h = h.lstrip("#")
                return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

            top_rgb = hex2rgb(mood["top"]) + (220,)
            bot_rgb = hex2rgb(mood["bot"]) + (220,)
            d.rectangle([0, 0, cur_sz, sl], fill=top_rgb)
            d.rectangle([0, sl, cur_sz, cur_sz], fill=bot_rgb)

            # Doira mask
            mask = Image.new("L", (cur_sz, cur_sz), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, cur_sz, cur_sz), fill=255)
            face_img.putalpha(mask)

            self._geo_cache = ImageTk.PhotoImage(face_img)

        jx = int(random.uniform(-1, 1)) if self.speaking else 0
        top_y = cy - R

        c.create_image(cx + jx, cy, image=self._geo_cache)

        # Ko'zlar
        for dx in (-0.30, 0.30):
            ex = int(cx + R * dx + jx)
            ey = int(cy - R * 0.20)
            er = max(int(R * 0.10), 4)
            c.create_oval(ex - er - 2, ey - er - 2, ex + er + 2, ey + er + 2,
                          fill="#c8dcff", outline="")
            c.create_oval(ex - er, ey - er, ex + er, ey + er,
                          fill="white", outline="")
            c.create_oval(ex - er // 2 + 2, ey - er // 2 + 2,
                          ex + er // 2 + 2, ey + er // 2 + 2,
                          fill="#1a3a6e", outline="")

        # Og'iz
        mh  = max(self.mouth_h * 0.8, 1.5)
        mw  = 8
        moy = int(cy + R * 0.30)
        col = "#1a3a6e" if mh > 5 else "#b4d2ff"
        c.create_oval(cx - mw + jx, moy - int(mh),
                      cx + mw + jx, moy + int(mh),
                      fill=col, outline="")
        if mh > 8:
            c.create_oval(cx - int(mw * 0.6) + jx, moy - int(mh * 0.65),
                          cx + int(mw * 0.6) + jx, moy + int(mh * 0.1),
                          fill="white", outline="")

    # ─────────────────────────────────────────────────────
    # Interaction Logic
    # ─────────────────────────────────────────────────────
    def write_log(self, text: str):
        if not self._running:
            return
        try:
            self.typing_queue.append(text)
            tl = text.lower()
            if "you:" in tl:
                self.status_text = "PROCESSING"
            elif "ai:" in tl:
                self.status_text = "GENERATING"
                self.start_speaking()
            if not self.is_typing:
                self._start_typing()

            try:
                from mobile_panel import get_panel
                panel = get_panel()
                if panel:
                    tag = "sys"
                    if "you:" in tl:
                        tag = "you"
                    elif "ai:" in tl:
                        tag = "ai"
                    panel.broadcast_log(text, tag=tag)
            except Exception:
                pass
        except:
            pass

    def _start_typing(self):
        if not self.typing_queue:
            self.is_typing   = False
            self.status_text = "SYSTEM READY"
            if self.speaking:
                self.stop_speaking()
            return
        self.is_typing = True
        self._type_char(self.typing_queue.popleft(), 0)

    def _type_char(self, text, i):
        if i == 0:
            self.log_text.configure(state="normal")
            tag = ("you" if "you:" in text.lower()
                   else "ai" if "ai:" in text.lower()
                   else "sys")
            self._current_tag = tag

        if i < len(text):
            self.log_text.insert(tk.END, text[i], self._current_tag)
            self.log_text.see(tk.END)
            self.root.after(10, self._type_char, text, i + 1)
        else:
            self.log_text.insert(tk.END, "\n")
            self.log_text.configure(state="disabled")
            self.root.after(30, self._start_typing)

    def start_speaking(self):
        if self._running:
            self.speaking = True

    def stop_speaking(self):
        self.speaking = False

    def _api_keys_exist(self):
        return API_FILE.exists()

    def wait_for_api_key(self):
        while not self._api_key_ready:
            time.sleep(0.1)

    def _show_setup_ui(self):
        self.setup = tk.Frame(
            self.root, bg=C_DIMMER,
            highlightbackground=C_PRI, highlightthickness=1)
        self.setup.place(relx=0.5, rely=0.5, anchor="center",
                         width=450, height=220)
        tk.Label(self.setup, text="◈ NEURAL INITIALISATION ◈",
                 fg=C_PRI, bg=C_DIMMER,
                 font=("Consolas", 12, "bold")).pack(pady=20)
        self.entry = tk.Entry(
            self.setup, width=40, fg=C_TEXT, bg="#000",
            borderwidth=1, highlightthickness=1, show="*")
        self.entry.pack(pady=10)
        tk.Button(
            self.setup, text="BOOT SYSTEM", command=self._save_api,
            bg=C_MID, fg="#fff", borderwidth=0,
            padx=20, pady=8).pack(pady=20)

    def _save_api(self):
        key = self.entry.get().strip()
        if not key:
            return
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(API_FILE, "w") as f:
            json.dump({"gemini_api_key": key}, f)
        self.setup.destroy()
        self._api_key_ready = True
        self.write_log("SYS: Systems fully operational. Malika Neural Core Online.")

    def _check_internet(self):
        try:
            t0 = time.time()
            # Fix: Use context manager to ensure socket is closed
            with socket.create_connection(("8.8.8.8", 53), timeout=3) as s:
                self._ping_ms   = int((time.time() - t0) * 1000)
                self.net_status = "ONLINE"
        except:
            self._ping_ms   = -1
            self.net_status = "OFFLINE"

    def _update_stats(self):
        if not self._running:
            return
        try:
            # NET
            self._stat_vars["NET"].set(self.net_status)

            # PING
            if self._ping_ms < 0:
                self._stat_vars["PING"].set("TIMEOUT")
            else:
                self._stat_vars["PING"].set(f"{self._ping_ms} ms")

            # TEZLIK — psutil bo'lsa haqiqiy, yo'q bo'lsa simulyatsiya
            try:
                import psutil
                counters = psutil.net_io_counters()
                cur  = counters.bytes_sent + counters.bytes_recv
                diff = cur - self._net_bytes_old
                self._net_bytes_old = cur
                if diff < 1024:
                    speed_str = f"{diff} B/s"
                elif diff < 1024 * 1024:
                    speed_str = f"{diff // 1024} KB/s"
                else:
                    speed_str = f"{diff // (1024 * 1024)} MB/s"
                self._net_speed_str = speed_str
            except ImportError:
                sim = int(50 + 80 * abs(math.sin(time.time() * 0.3)))
                if self.speaking:
                    sim += random.randint(100, 400)
                self._net_speed_str = f"{sim} KB/s"
            self._stat_vars["TEZLIK"].set(self._net_speed_str)

            # KAYFIYAT
            self._stat_vars["KAYFIYAT"].set(self.mood.upper())

            # STATUS
            self._stat_vars["STATUS"].set(
                "ANALYZING" if self.speaking else self.status_text)

        except Exception:
            pass

        if self._running:
            self.root.after(1000, self._update_stats)


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    face = sys.argv[1] if len(sys.argv) > 1 else ""
    ui   = JarvisUI(face_path=face)
    ui.root.mainloop()