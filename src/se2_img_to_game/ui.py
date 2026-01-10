import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from .processing import generate_blocks_with_allowed, generate_instructions_from_blocks, generate_schematic_image_from_blocks, calculate_target_dimensions
from .locales import LANG_STRINGS
import sys
import json
import csv

# ===================== Configuração de Estilo =====================
def setup_styles(mode="light"):
    style = ttk.Style()
    style.theme_use("clam")
    default_font = ("Segoe UI", 10)
    style.configure("TButton", font=default_font, padding=5)
    style.configure("TLabel", font=default_font)
    style.configure("TEntry", font=default_font)
    style.configure("TCheckbutton", font=default_font)
    style.configure("Treeview", font=default_font, rowheight=25)
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
    style.configure("TFrame", background="#f0f0f0")
    if mode == "dark":
        dark_bg = "#121212"
        dark_fg = "#e0e0e0"
        style.configure("TLabel", background=dark_bg, foreground=dark_fg)
        style.configure("TButton", background=dark_bg, foreground=dark_fg)
        style.map("TButton", background=[("active", dark_bg)])
        style.configure("TEntry", fieldbackground=dark_bg, foreground=dark_fg)
        style.configure("TCheckbutton", background=dark_bg, foreground=dark_fg)
        style.configure("Treeview", background=dark_bg, foreground=dark_fg, fieldbackground=dark_bg)
        style.configure("Treeview.Heading", background="#2e2e2e", foreground="#ffffff")
        style.configure("TFrame", background=dark_bg)
    else:
        light_bg = "#f0f0f0"
        light_fg = "#000000"
        style.configure("TLabel", background=light_bg, foreground=light_fg)
        style.configure("TButton", background=light_bg, foreground=light_fg)
        style.map("TButton", background=[("active", light_bg)])
        style.configure("TEntry", fieldbackground=light_bg, foreground=light_fg)
        style.configure("TCheckbutton", background=light_bg, foreground=light_fg)
        style.configure("Treeview", background=light_bg, foreground=light_fg, fieldbackground=light_bg)
        style.configure("Treeview.Heading", background="#d9d9d9", foreground=light_fg)
        style.configure("TFrame", background=light_bg)

# ===================== Visualizador com Zoom =====================
class ZoomWindow(tk.Toplevel):
    def __init__(self, parent, image):
        super().__init__(parent)
        self.title(self.master.strings["zoom_title"])
        self.original_image = image
        self.zoom_factor = 1.0
        self.create_widgets()
        self.canvas.bind("<Configure>", self.on_configure)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)
        self.canvas.bind("<Button-5>", self.on_mousewheel)
        self.bind("<KeyPress-plus>", self.on_key_zoom_in)
        self.bind("<KeyPress-equal>", self.on_key_zoom_in)
        self.bind("<KeyPress-minus>", self.on_key_zoom_out)
        self.bind("<KeyPress-KP_Add>", self.on_key_zoom_in)
        self.bind("<KeyPress-KP_Subtract>", self.on_key_zoom_out)
        self.update_image()
        self.canvas.focus_set()

    def create_widgets(self):
        frame_buttons = ttk.Frame(self)
        frame_buttons.pack(pady=5)
        btn_zoom_in = ttk.Button(frame_buttons, text="Zoom In", command=self.zoom_in)
        btn_zoom_in.pack(side=tk.LEFT, padx=5)
        btn_zoom_out = ttk.Button(frame_buttons, text="Zoom Out", command=self.zoom_out)
        btn_zoom_out.pack(side=tk.LEFT, padx=5)
        btn_reset = ttk.Button(frame_buttons, text="Reset Zoom", command=self.reset_zoom)
        btn_reset.pack(side=tk.LEFT, padx=5)
        self.canvas = tk.Canvas(self, bg="black")
        self.h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)
        self.h_scroll.pack(side="bottom", fill="x")
        self.v_scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

    def on_configure(self, event):
        max_size = 400
        factor = min(max_size / self.original_image.width, max_size / self.original_image.height, 1)
        self.zoom_factor = factor
        self.update_image()

    def on_button_press(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def on_move_press(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_mousewheel(self, event):
        if hasattr(event, 'delta'):
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            if event.num == 4:
                self.zoom_in()
            elif event.num == 5:
                self.zoom_out()

    def on_key_zoom_in(self, event):
        self.zoom_in()

    def on_key_zoom_out(self, event):
        self.zoom_out()

    def update_image(self):
        new_width = int(self.original_image.width * self.zoom_factor)
        new_height = int(self.original_image.height * self.zoom_factor)
        self.zoomed_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.zoomed_image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def zoom_in(self):
        self.zoom_factor *= 1.2
        self.update_image()

    def zoom_out(self):
        self.zoom_factor /= 1.2
        self.update_image()

    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.update_image()

# ===================== Interface Gráfica Principal =====================
class PixelArtSchematicApp(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.debug_var = tk.BooleanVar(value=False)
        self.lang = "pt"
        self.theme_mode = "light"
        self.strings = LANG_STRINGS[self.lang]
        self.master.title(self.strings["title"])
        self.master.geometry("1100x800")
        self.image_pil = None
        self.blocks = []
        self.instructions = []
        self.schematic = None
        self.block_size = 20

        # High DPI check
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass

        setup_styles(self.theme_mode)
        self.create_widgets()
        self.create_menu()
        self.pack(expand=True, fill="both")

    def create_menu(self):
        menubar = tk.Menu(self.master)
        language_menu = tk.Menu(menubar, tearoff=0)
        language_menu.add_command(label=LANG_STRINGS["pt"]["pt"], command=lambda: self.set_language("pt"))
        language_menu.add_command(label=LANG_STRINGS["pt"]["en"], command=lambda: self.set_language("en"))
        menubar.add_cascade(label=self.strings["language"], menu=language_menu)
        theme_menu = tk.Menu(menubar, tearoff=0)
        theme_menu.add_command(label=LANG_STRINGS["pt"]["light"], command=lambda: self.set_theme("light"))
        theme_menu.add_command(label=LANG_STRINGS["pt"]["dark"], command=lambda: self.set_theme("dark"))
        menubar.add_cascade(label=self.strings["theme"], menu=theme_menu)
        self.master.config(menu=menubar)

    def set_language(self, lang):
        self.lang = lang
        self.strings = LANG_STRINGS[self.lang]
        self.master.title(self.strings["title"])
        self.update_labels()

    def set_theme(self, mode):
        self.theme_mode = mode
        setup_styles(mode)
        if mode == "dark":
            self.master.configure(bg="#121212")
        else:
            self.master.configure(bg="#f0f0f0")

    def update_labels(self):
        self.label_z.config(text=self.strings["value_z"])
        self.label_y.config(text=self.strings["value_y"])
        self.btn_load.config(text=self.strings["load_image"])
        self.btn_generate.config(text=self.strings["generate_scheme"])
        self.btn_save.config(text=self.strings["save_scheme"])
        self.btn_save_data.config(text="Salvar Dados" if self.lang=="pt" else "Save Data")
        self.btn_zoom.config(text=self.strings["visualize_details"])
        self.label_total.config(text=f"{self.strings['total_blocks']} 0")
        self.tree.heading("type", text=self.strings["block_summary"])
        self.tree.heading("count", text=self.strings["count"])
        self.lbl_exclude.config(text=self.strings["exclude_blocks"])
        self.cb_edge_label.config(text=self.strings["edge_pref"])
        self.cb_interior_label.config(text=self.strings["interior_pref"])
        self.cb_use_pref_label.config(text=self.strings["use_pref"])
        self.cb_thickness_label.config(text=self.strings["thickness_3d"])

    def create_widgets(self):
        # Frame for Input
        frame_input = ttk.LabelFrame(self, text="Input", padding=10)
        frame_input.pack(pady=5, padx=10, fill="x")

        self.btn_load = ttk.Button(frame_input, text=self.strings["load_image"], command=self.load_image)
        self.btn_load.grid(row=0, column=0, padx=5)

        self.label_z = ttk.Label(frame_input, text=self.strings["value_z"])
        self.label_z.grid(row=0, column=1, padx=5)
        self.entry_z = ttk.Entry(frame_input, width=10)
        self.entry_z.insert(0, "")
        self.entry_z.grid(row=0, column=2, padx=5)

        self.label_y = ttk.Label(frame_input, text=self.strings["value_y"])
        self.label_y.grid(row=0, column=3, padx=5)
        self.entry_y = ttk.Entry(frame_input, width=10)
        self.entry_y.insert(0, "")
        self.entry_y.grid(row=0, column=4, padx=5)

        self.checkbox_debug = ttk.Checkbutton(frame_input, text="Debug", variable=self.debug_var)
        self.checkbox_debug.grid(row=0, column=5, padx=5)

        # Frame for Processing Options
        frame_proc = ttk.LabelFrame(self, text="Processing Options", padding=10)
        frame_proc.pack(pady=5, padx=10, fill="x")

        # Threshold Slider
        ttk.Label(frame_proc, text="Threshold (Sensitivity):").grid(row=0, column=0, padx=5)
        self.threshold_var = tk.DoubleVar(value=30.0)
        self.scale_thresh = ttk.Scale(frame_proc, from_=0, to=100, orient="horizontal", variable=self.threshold_var)
        self.scale_thresh.grid(row=0, column=1, padx=5, sticky="ew")

        # Alpha Threshold Slider
        ttk.Label(frame_proc, text="Alpha Threshold:").grid(row=0, column=2, padx=5)
        self.alpha_thresh_var = tk.DoubleVar(value=128.0)
        self.scale_alpha_thresh = ttk.Scale(frame_proc, from_=0, to=255, orient="horizontal", variable=self.alpha_thresh_var)
        self.scale_alpha_thresh.grid(row=0, column=3, padx=5, sticky="ew")

        # Block Types
        self.lbl_exclude = ttk.Label(frame_proc, text=self.strings["exclude_blocks"])
        self.lbl_exclude.grid(row=1, column=0, padx=5, pady=5)

        frame_checks = ttk.Frame(frame_proc)
        frame_checks.grid(row=1, column=1, columnspan=3, sticky="w")

        self.include_25_var = tk.BooleanVar(value=True)
        self.include_50_var = tk.BooleanVar(value=True)
        self.include_2_5_var = tk.BooleanVar(value=True)
        self.cb_include_25 = ttk.Checkbutton(frame_checks, text=self.strings["include_25"], variable=self.include_25_var)
        self.cb_include_25.pack(side="left", padx=5)
        self.cb_include_50 = ttk.Checkbutton(frame_checks, text=self.strings["include_50"], variable=self.include_50_var)
        self.cb_include_50.pack(side="left", padx=5)
        self.cb_include_2_5 = ttk.Checkbutton(frame_checks, text=self.strings["include_2_5"], variable=self.include_2_5_var)
        self.cb_include_2_5.pack(side="left", padx=5)

        # Preferences (Edge/Interior) - kept for backward compat logic if desired,
        # though optimized logic relies less on this and more on packing.
        # But we still keep the UI.

        self.cb_use_pref_var = tk.BooleanVar(value=False)
        self.cb_use_pref = ttk.Checkbutton(frame_proc, variable=self.cb_use_pref_var)
        self.cb_use_pref.grid(row=2, column=0, padx=5)
        self.cb_use_pref_label = ttk.Label(frame_proc, text=self.strings["use_pref"])
        self.cb_use_pref_label.grid(row=2, column=1, padx=5, sticky="w")

        self.cb_edge_label = ttk.Label(frame_proc, text=self.strings["edge_pref"])
        self.cb_edge_label.grid(row=3, column=0, padx=5)
        self.combo_edge = ttk.Combobox(frame_proc, values=["2.5m", "50cm", "25cm"], state="readonly", width=10)
        self.combo_edge.set("2.5m")
        self.combo_edge.grid(row=3, column=1, padx=5, sticky="w")

        self.cb_interior_label = ttk.Label(frame_proc, text=self.strings["interior_pref"])
        self.cb_interior_label.grid(row=3, column=2, padx=5)
        self.combo_interior = ttk.Combobox(frame_proc, values=["2.5m", "50cm", "25cm"], state="readonly", width=10)
        self.combo_interior.set("50cm")
        self.combo_interior.grid(row=3, column=3, padx=5, sticky="w")

        self.cb_3d_var = tk.BooleanVar(value=False)
        self.cb_3d = ttk.Checkbutton(frame_proc, text=self.strings["thickness_3d"], variable=self.cb_3d_var)
        self.cb_3d.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        self.btn_generate = ttk.Button(frame_proc, text=self.strings["generate_scheme"], command=self.process_image)
        self.btn_generate.grid(row=5, column=0, columnspan=4, pady=10)

        # Output Info
        self.lbl_output_res = ttk.Label(frame_proc, text="Calculated Grid: -")
        self.lbl_output_res.grid(row=6, column=0, columnspan=4, sticky="w", padx=5)

        # Tabela de resumo
        frame_table = ttk.Frame(self)
        frame_table.pack(expand=True, fill="both", padx=10, pady=10)
        self.tree = ttk.Treeview(frame_table, columns=("type", "count"), show="headings")
        self.tree.heading("type", text=self.strings["block_summary"])
        self.tree.heading("count", text=self.strings["count"])
        self.tree.column("type", width=150, anchor="center")
        self.tree.column("count", width=150, anchor="center")
        scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(expand=True, fill="both")

        self.label_total = ttk.Label(self, text=f"{self.strings['total_blocks']} 0", font=("Segoe UI", 12, "bold"))
        self.label_total.pack(pady=5)

        frame_actions = ttk.Frame(self)
        frame_actions.pack(pady=5)
        self.btn_save = ttk.Button(frame_actions, text=self.strings["save_scheme"], command=self.save_scheme)
        self.btn_save.pack(side="left", padx=5)
        self.btn_save_data = ttk.Button(frame_actions, text="Salvar Dados", command=self.save_data)
        self.btn_save_data.pack(side="left", padx=5)
        self.btn_zoom = ttk.Button(frame_actions, text=self.strings["visualize_details"], command=self.zoom_scheme)
        self.btn_zoom.pack(side="left", padx=5)

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Selecione a Imagem",
            filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("Todos os arquivos", "*.*")]
        )
        if file_path:
            try:
                # Use RGBA for transparency support
                self.image_pil = Image.open(file_path).convert("RGBA")
                messagebox.showinfo(self.strings["load_image"], f"{self.strings['load_success']} {file_path}")
                # Update expected resolution if Z is set
                self.update_resolution_label()
            except Exception as e:
                messagebox.showerror(self.strings["error"], f"Erro ao carregar a imagem:\n{e}")

    def update_resolution_label(self):
        if self.image_pil:
            z_str = self.entry_z.get().strip()
            y_str = self.entry_y.get().strip()
            try:
                z = float(z_str) if z_str else 0
                y = float(y_str) if y_str else None
                if z > 0:
                    w, h = calculate_target_dimensions(self.image_pil.size, z, y)
                    self.lbl_output_res.config(text=f"Calculated Grid: {w} x {h} blocks (0.25m unit)")
            except:
                pass

    def process_image(self):
        if self.image_pil is None:
            messagebox.showwarning(self.strings["warning"], "Carregue uma imagem primeiro!")
            return
        z_str = self.entry_z.get().strip()
        if not z_str:
            messagebox.showerror(self.strings["error"], "Informe o valor de Z (em metros)!")
            return
        try:
            real_z = float(z_str)
        except ValueError:
            messagebox.showerror(self.strings["error"], "Valor de Z inválido. Exemplo: 32.74")
            return
        y_str = self.entry_y.get().strip()
        if y_str == "":
            real_y = 0.0
            y_val_for_calc = None
        else:
            try:
                real_y = float(y_str)
                y_val_for_calc = real_y
            except ValueError:
                messagebox.showerror(self.strings["error"], "Valor de Y inválido. Informe um número.")
                return

        img_height = self.image_pil.height
        scale = real_z / img_height
        if self.debug_var.get():
            print(f"Escala: {scale:.4f} m/px (Z = {real_z} m; altura = {img_height} px)")

        # Update label
        self.update_resolution_label()

        # Define os tipos permitidos com base nos checkbuttons.
        allowed = []
        if self.include_25_var.get():
            allowed.append("25cm")
        if self.include_50_var.get():
            allowed.append("50cm")
        if self.include_2_5_var.get():
            allowed.append("2.5m")

        # Gera os blocos usando somente os tipos permitidos.
        # Note: We pass the threshold from the slider
        thresh_val = self.threshold_var.get()
        alpha_val = self.alpha_thresh_var.get()

        self.blocks, small_px, new_width, new_height, num_rows, num_cols, inside = generate_blocks_with_allowed(
            self.image_pil, scale, allowed, threshold=thresh_val, debug=self.debug_var.get(), alpha_thresh=alpha_val)

        if not self.blocks:
            messagebox.showinfo(self.strings["warning"], "Nenhum bloco gerado (possivelmente nenhum tipo permitido).")
            return

        # Se o toggle de preferências estiver ativo, aplica as preferências para borda/interior.
        if self.cb_use_pref_var.get():
            def is_edge_block(block):
                r0 = block["row_start"]
                c0 = block["col_start"]
                size = block["cell_size"]
                if r0 == 0 or c0 == 0 or (r0 + size) >= num_rows or (c0 + size) >= num_cols:
                    return True
                for i in range(r0, r0 + size):
                    for j in range(c0, c0 + size):
                        if not inside[i][j]:
                            return True
                return False
            for block in self.blocks:
                desired = self.combo_edge.get() if is_edge_block(block) else self.combo_interior.get()
                # Se o tipo desejado estiver entre os permitidos, usa-o; caso contrário, mantém o tipo atual.
                if desired in allowed:
                    block["block_type"] = desired

        # Generate instructions (and store them in self.instructions for saving)
        self.instructions = generate_instructions_from_blocks(self.blocks, small_px, scale, real_y, use_3d=self.cb_3d_var.get())
        summary = {}
        for inst in self.instructions:
            bt = inst["block_type"]
            summary[bt] = summary.get(bt, 0) + 1
        for item in self.tree.get_children():
            self.tree.delete(item)
        for bt, count in summary.items():
            self.tree.insert("", tk.END, values=(bt, count))
        total_blocks = sum(summary.values())
        self.label_total.config(text=f"{self.strings['total_blocks']} {total_blocks}")
        messagebox.showinfo(self.strings["generate_scheme"], self.strings["scheme_generated"])
        self.schematic = generate_schematic_image_from_blocks((new_width, new_height), self.blocks, small_px)
        self.show_preview()

    def include_block_type(self, block_type):
        if block_type == "25cm":
            return self.include_25_var.get()
        elif block_type == "50cm":
            return self.include_50_var.get()
        elif block_type == "2.5m":
            return self.include_2_5_var.get()
        return False

    def show_preview(self):
        preview_window = tk.Toplevel(self)
        preview_window.title(self.strings["preview_title"])
        preview_img = self.schematic.copy()
        preview_img.thumbnail((400, 400))
        preview_photo = ImageTk.PhotoImage(preview_img)
        label = ttk.Label(preview_window, image=preview_photo)
        label.image = preview_photo
        label.pack(padx=10, pady=10)

    def save_scheme(self):
        if self.schematic is None:
            messagebox.showwarning(self.strings["warning"], "Nenhum esquema gerado para salvar!")
            return
        file_path = filedialog.asksaveasfilename(
            title="Salvar Esquema" if self.lang=="pt" else "Save Scheme",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("Todos os arquivos", "*.*")]
        )
        if file_path:
            try:
                self.schematic.save(file_path)
                messagebox.showinfo("Salvo" if self.lang=="pt" else "Saved",
                                    f"{'Esquema salvo com sucesso em:' if self.lang=='pt' else 'Scheme saved successfully at:'}\n{file_path}")
            except Exception as e:
                messagebox.showerror(self.strings["error"], f"Erro ao salvar o esquema:\n{e}")

    def save_data(self):
        if not self.instructions:
            messagebox.showwarning(self.strings["warning"], "Nenhum dado gerado para salvar!")
            return
        file_path = filedialog.asksaveasfilename(
            title="Salvar Dados" if self.lang=="pt" else "Save Data",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("CSV", "*.csv"), ("Todos os arquivos", "*.*")]
        )
        if file_path:
            try:
                if file_path.lower().endswith(".csv"):
                    # Save as CSV
                    keys = self.instructions[0].keys()
                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        dict_writer = csv.DictWriter(f, keys)
                        dict_writer.writeheader()
                        dict_writer.writerows(self.instructions)
                else:
                    # Save as JSON (Default)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.instructions, f, indent=4)

                messagebox.showinfo("Salvo" if self.lang=="pt" else "Saved",
                                    f"{'Dados salvos com sucesso em:' if self.lang=='pt' else 'Data saved successfully at:'}\n{file_path}")
            except Exception as e:
                messagebox.showerror(self.strings["error"], f"Erro ao salvar os dados:\n{e}")

    def zoom_scheme(self):
        if self.schematic is None:
            messagebox.showwarning(self.strings["warning"], "Nenhum esquema gerado para visualizar!")
            return
        ZoomWindow(self, self.schematic)
