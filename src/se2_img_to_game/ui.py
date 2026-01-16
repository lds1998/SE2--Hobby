import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import json
import csv
import threading
from . import processing
from .locales import STRINGS

class SE2App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lang = "en"
        self.s = STRINGS[self.lang]

        self.title(self.s["title"])
        self.geometry("1000x800")

        self.image_raw = None
        self.blocks = []
        self.instructions = []
        self.preview_img = None

        self._setup_ui()

    def _setup_ui(self):
        # Styles
        style = ttk.Style()
        style.theme_use('clam')

        # Main Container
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        # 1. Input Section
        frm_input = ttk.LabelFrame(main, text=self.s["grp_input"], padding=10)
        frm_input.pack(fill="x", pady=5)

        ttk.Button(frm_input, text=self.s["lbl_load"], command=self.load_image).pack(side="left", padx=5)

        ttk.Label(frm_input, text=self.s["lbl_z"]).pack(side="left", padx=5)
        self.var_z = tk.DoubleVar(value=50.0)
        ttk.Entry(frm_input, textvariable=self.var_z, width=8).pack(side="left")

        # New Width X Input
        ttk.Label(frm_input, text=self.s["lbl_x"]).pack(side="left", padx=5)
        self.var_x = tk.DoubleVar(value=0.0) # 0 means auto
        ttk.Entry(frm_input, textvariable=self.var_x, width=8).pack(side="left")

        ttk.Label(frm_input, text=self.s["lbl_y_pos"]).pack(side="left", padx=5)
        self.var_y_pos = tk.DoubleVar(value=0.0)
        ttk.Entry(frm_input, textvariable=self.var_y_pos, width=8).pack(side="left")

        # 2. Processing Section
        frm_proc = ttk.LabelFrame(main, text=self.s["grp_proc"], padding=10)
        frm_proc.pack(fill="x", pady=5)

        # Thresholds
        frm_thresh = ttk.Frame(frm_proc)
        frm_thresh.pack(fill="x", pady=2)

        ttk.Label(frm_thresh, text=self.s["lbl_thresh"]).pack(side="left")
        self.var_thresh = tk.DoubleVar(value=30.0)
        ttk.Scale(frm_thresh, from_=0, to=100, variable=self.var_thresh).pack(side="left", fill="x", expand=True, padx=5)

        ttk.Label(frm_thresh, text=self.s["lbl_alpha"]).pack(side="left")
        self.var_alpha = tk.DoubleVar(value=128.0)
        ttk.Scale(frm_thresh, from_=0, to=255, variable=self.var_alpha).pack(side="left", fill="x", expand=True, padx=5)

        # Blocks & Edge
        frm_opts = ttk.Frame(frm_proc)
        frm_opts.pack(fill="x", pady=5)

        ttk.Label(frm_opts, text=self.s["lbl_blocks"]).pack(side="left")
        self.var_25cm = tk.BooleanVar(value=True)
        self.var_50cm = tk.BooleanVar(value=True)
        self.var_250cm = tk.BooleanVar(value=True)

        ttk.Checkbutton(frm_opts, text="25cm", variable=self.var_25cm).pack(side="left", padx=2)
        ttk.Checkbutton(frm_opts, text="50cm", variable=self.var_50cm).pack(side="left", padx=2)
        ttk.Checkbutton(frm_opts, text="2.5m", variable=self.var_250cm).pack(side="left", padx=2)

        ttk.Label(frm_opts, text=self.s["lbl_edge"]).pack(side="left", padx=10)
        self.var_edge = tk.StringVar(value="None")
        ttk.Combobox(frm_opts, textvariable=self.var_edge, values=["None", "25cm", "50cm", "2.5m"], state="readonly", width=8).pack(side="left")

        self.btn_process = ttk.Button(frm_proc, text=self.s["btn_gen"], command=self.start_processing)
        self.btn_process.pack(fill="x", pady=5)

        # 3. Output Section
        frm_out = ttk.LabelFrame(main, text=self.s["grp_out"], padding=10)
        frm_out.pack(fill="both", expand=True, pady=5)

        # Split: Left (Data), Right (Preview)
        paned = ttk.PanedWindow(frm_out, orient="horizontal")
        paned.pack(fill="both", expand=True)

        frm_data = ttk.Frame(paned)
        paned.add(frm_data, weight=1)

        # Treeview
        self.tree = ttk.Treeview(frm_data, columns=("type", "count"), show="headings", height=10)
        self.tree.heading("type", text="Type")
        self.tree.heading("count", text="Count")
        self.tree.pack(fill="both", expand=True)

        self.lbl_total = ttk.Label(frm_data, text="Total: 0")
        self.lbl_total.pack(pady=5)

        btn_frame = ttk.Frame(frm_data)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text=self.s["btn_save_img"], command=self.save_image).pack(side="left", fill="x", expand=True)
        ttk.Button(btn_frame, text=self.s["btn_save_data"], command=self.save_data).pack(side="left", fill="x", expand=True)

        # Preview
        self.cv_preview = tk.Canvas(paned, bg="gray")
        paned.add(self.cv_preview, weight=3)

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if path:
            self.image_raw = Image.open(path).convert("RGBA")
            messagebox.showinfo("Loaded", f"Loaded: {self.image_raw.size}")

    def start_processing(self):
        if not self.image_raw:
            return

        self.btn_process.config(state="disabled", text="Processing...")

        # Capture inputs in main thread
        inputs = {
            'z': self.var_z.get(),
            'x': self.var_x.get(),
            'y_pos': self.var_y_pos.get(),
            'allowed': [],
            'edge': self.var_edge.get(),
            'thresh': self.var_thresh.get(),
            'alpha': self.var_alpha.get(),
            'img': self.image_raw.copy() # Thread safe copy
        }

        if self.var_25cm.get(): inputs['allowed'].append("25cm")
        if self.var_50cm.get(): inputs['allowed'].append("50cm")
        if self.var_250cm.get(): inputs['allowed'].append("2.5m")
        if inputs['edge'] == "None": inputs['edge'] = None

        thread = threading.Thread(target=self.run_processing, args=(inputs,), daemon=True)
        thread.start()

    def run_processing(self, inputs):
        try:
            scale = inputs['z'] / inputs['img'].height

            blocks, tw, th = processing.generate_blocks(
                inputs['img'], inputs['allowed'], scale,
                threshold=inputs['thresh'],
                alpha_thresh=inputs['alpha'],
                edge_pref=inputs['edge'],
                width_m=inputs['x']
            )

            instructions = processing.generate_instructions(blocks, inputs['y_pos'])

            # Schedule UI update
            self.after(0, self.processing_complete, blocks, instructions, tw, th)

        except Exception as e:
            self.after(0, self.processing_error, str(e))

    def processing_complete(self, blocks, instructions, tw, th):
        self.blocks = blocks
        self.instructions = instructions
        self.update_tree()
        self.update_preview(tw, th)
        self.btn_process.config(state="normal", text=self.s["btn_gen"])

    def processing_error(self, msg):
        messagebox.showerror("Error", msg)
        self.btn_process.config(state="normal", text=self.s["btn_gen"])

    def update_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        counts = {}
        for b in self.blocks:
            t = b['block_type']
            counts[t] = counts.get(t, 0) + 1

        for t, c in counts.items():
            self.tree.insert("", "end", values=(t, c))

        self.lbl_total.config(text=f"Total: {len(self.blocks)}")

    def update_preview(self, w, h):
        img = processing.generate_preview(w, h, self.blocks)
        # Resize for display
        display_h = 500
        aspect = w / h
        display_w = int(display_h * aspect)

        img_disp = img.resize((display_w, display_h), Image.Resampling.NEAREST)
        self.preview_tk = ImageTk.PhotoImage(img_disp)

        self.cv_preview.delete("all")
        cw = self.cv_preview.winfo_width()
        ch = self.cv_preview.winfo_height()
        self.cv_preview.create_image(cw//2, ch//2, image=self.preview_tk)

    def save_image(self):
        if not self.blocks: return
        path = filedialog.asksaveasfilename(defaultextension=".png")
        if path:
            max_x = max(b['x'] + b['w'] for b in self.blocks)
            max_y = max(b['y'] + b['h'] for b in self.blocks)
            img = processing.generate_preview(max_x, max_y, self.blocks)
            img.save(path)

    def save_data(self):
        if not self.instructions: return
        path = filedialog.asksaveasfilename(filetypes=[("JSON", "*.json"), ("CSV", "*.csv")])
        if path:
            if path.endswith(".csv"):
                with open(path, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Type", "X", "Y", "Z", "W", "H", "D"])
                    for i in self.instructions:
                        p = i['position']
                        s = i['size']
                        writer.writerow([i['block_type'], p['x'], p['y'], p['z'], s['width'], s['height'], s['depth']])
            else:
                with open(path, "w") as f:
                    json.dump(self.instructions, f, indent=2)
