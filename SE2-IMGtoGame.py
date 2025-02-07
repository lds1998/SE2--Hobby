import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
import numpy as np

# ===================== Dicionários de Idiomas =====================
LANG_STRINGS = {
    "pt": {
        "title": "Gerador de Esquema de Pixel Art para Space Engineers 2",
        "load_image": "Carregar Imagem",
        "value_z": "Valor Z (m) [obrigatório]:",
        "value_y": "Valor Y (m) [opcional]:",
        "generate_scheme": "Gerar Esquema",
        "save_scheme": "Salvar Esquema",
        "preview_title": "Pré-visualização do Esquema",
        "zoom_title": "Visualização com Zoom",
        "visualize_details": "Visualizar Detalhes",
        "block_summary": "Resumo dos Blocos",
        "total_blocks": "Total de blocos:",
        "error": "Erro",
        "warning": "Aviso",
        "load_success": "Imagem carregada com sucesso:",
        "scheme_generated": "Esquema gerado com sucesso!",
        "language": "Idioma",
        "pt": "Português",
        "en": "English",
        "count": "Quantidade",
        "theme": "Tema",
        "light": "Light",
        "dark": "Dark"
    },
    "en": {
        "title": "Pixel Art Scheme Generator for Space Engineers 2",
        "load_image": "Load Image",
        "value_z": "Value Z (m) [required]:",
        "value_y": "Value Y (m) [optional]:",
        "generate_scheme": "Generate Scheme",
        "save_scheme": "Save Scheme",
        "preview_title": "Scheme Preview",
        "zoom_title": "Zoom Preview",
        "visualize_details": "View Details",
        "block_summary": "Block Summary",
        "total_blocks": "Total blocks:",
        "error": "Error",
        "warning": "Warning",
        "load_success": "Image loaded successfully:",
        "scheme_generated": "Scheme generated successfully!",
        "language": "Language",
        "pt": "Portuguese",
        "en": "English",
        "count": "Count",
        "theme": "Theme",
        "light": "Light",
        "dark": "Dark"
    }
}

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

# ===================== Funções de Processamento =====================

def compute_shape_mask(image, shape_thresh=250):
    gray = image.convert("L")
    arr = np.array(gray)
    mask = arr < shape_thresh
    return mask

def generate_blocks_greedy(image_pil, scale, threshold=30.0, debug=False):
    small_px = int(round(0.25 / scale))
    if small_px <= 0:
        small_px = 1
    width, height = image_pil.size
    num_cols = width // small_px
    num_rows = height // small_px
    new_width = num_cols * small_px
    new_height = num_rows * small_px
    image_resized = image_pil.resize((new_width, new_height))
    mask = compute_shape_mask(image_resized, shape_thresh=250)
    inside = np.zeros((num_rows, num_cols), dtype=bool)
    for r in range(num_rows):
        for c in range(num_cols):
            cell_mask = mask[r*small_px:(r+1)*small_px, c*small_px:(c+1)*small_px]
            inside[r, c] = (cell_mask.mean() > 0.5)
    img_np = np.array(image_resized, dtype=np.float32)
    cell_colors = np.zeros((num_rows, num_cols, 3), dtype=np.float32)
    for r in range(num_rows):
        for c in range(num_cols):
            cell = img_np[r*small_px:(r+1)*small_px, c*small_px:(c+1)*small_px, :]
            cell_colors[r, c] = cell.mean(axis=(0,1))
    merged = np.zeros((num_rows, num_cols), dtype=bool)
    blocks = []
    # Blocos grandes: 10x10 células → 2.5 m
    large_size = 10
    large_threshold = 50.0
    for r in range(num_rows - large_size + 1):
        for c in range(num_cols - large_size + 1):
            if not inside[r:r+large_size, c:c+large_size].all():
                continue
            if merged[r:r+large_size, c:c+large_size].any():
                continue
            region = cell_colors[r:r+large_size, c:c+large_size]
            avg = region.mean(axis=(0,1))
            diff = np.abs(region - avg)
            if diff.max() <= large_threshold:
                merged[r:r+large_size, c:c+large_size] = True
                blocks.append({
                    "row_start": r,
                    "col_start": c,
                    "cell_size": large_size,
                    "avg_color": avg,
                    "block_type": "2.5m"
                })
    # Blocos médios: 2x2 células → 50 cm
    med_size = 2
    med_threshold = 30.0
    for r in range(num_rows - med_size + 1):
        for c in range(num_cols - med_size + 1):
            if not inside[r:r+med_size, c:c+med_size].all():
                continue
            if merged[r:r+med_size, c:c+med_size].any():
                continue
            region = cell_colors[r:r+med_size, c:c+med_size]
            avg = region.mean(axis=(0,1))
            diff = np.abs(region - avg)
            if diff.max() <= med_threshold:
                merged[r:r+med_size, c:c+med_size] = True
                blocks.append({
                    "row_start": r,
                    "col_start": c,
                    "cell_size": med_size,
                    "avg_color": avg,
                    "block_type": "50cm"
                })
    # Blocos pequenos: 1x1 células → 25 cm
    for r in range(num_rows):
        for c in range(num_cols):
            if not inside[r, c]:
                continue
            if not merged[r, c]:
                merged[r, c] = True
                avg = cell_colors[r, c]
                blocks.append({
                    "row_start": r,
                    "col_start": c,
                    "cell_size": 1,
                    "avg_color": avg,
                    "block_type": "25cm"
                })
    if debug:
        total_cells = num_rows * num_cols
        print(f"Total de células: {total_cells}, Blocos gerados: {len(blocks)}")
    return blocks, small_px, new_width, new_height, num_rows, num_cols

def generate_instructions_from_blocks(blocks, small_px, scale, constant_y):
    instructions = []
    for block in blocks:
        r = block["row_start"]
        c = block["col_start"]
        size = block["cell_size"]
        x0_px = c * small_px
        y0_px = r * small_px
        width_px = size * small_px
        height_px = size * small_px
        center_x = (x0_px + width_px/2) * scale
        center_z = (y0_px + height_px/2) * scale
        instructions.append({
            "block_type": block["block_type"],
            "x": round(center_x, 2),
            "y": constant_y,
            "z": round(center_z, 2),
            "width": round(width_px * scale, 2),
            "height": round(height_px * scale, 2)
        })
    return instructions

def generate_schematic_image_from_blocks(image_size, blocks, small_px):
    schematic = Image.new("RGB", image_size, "white")
    draw = ImageDraw.Draw(schematic)
    for block in blocks:
        r = block["row_start"]
        c = block["col_start"]
        size = block["cell_size"]
        x0 = c * small_px
        y0 = r * small_px
        x1 = x0 + size * small_px
        y1 = y0 + size * small_px
        draw.rectangle([x0, y0, x1, y1], outline="black", width=1)
    return schematic

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
        self.h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.v_scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    def on_configure(self, event):
        # Aqui usamos um tamanho máximo fixo para preview na janela de zoom
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        factor = min(cw / self.original_image.width, ch / self.original_image.height)
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
        self.lang = "pt"  # Idioma padrão
        self.theme_mode = "light"
        self.strings = LANG_STRINGS[self.lang]
        self.master.title(self.strings["title"])
        self.master.geometry("1100x750")
        self.image_pil = None
        self.blocks = []
        self.instructions = []
        self.schematic = None
        self.block_size = 20
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
        self.btn_zoom.config(text=self.strings["visualize_details"])
        self.label_total.config(text=f"{self.strings['total_blocks']} 0")
        self.tree.heading("type", text=self.strings["block_summary"])
        self.tree.heading("count", text=self.strings["count"])
    
    def create_widgets(self):
        # Utilizando ttk.Frame para manter os estilos
        frame_controls = ttk.Frame(self)
        frame_controls.pack(pady=10)
        
        self.btn_load = ttk.Button(frame_controls, text=self.strings["load_image"], command=self.load_image)
        self.btn_load.grid(row=0, column=0, padx=5)
        
        self.label_z = ttk.Label(frame_controls, text=self.strings["value_z"])
        self.label_z.grid(row=0, column=1, padx=5)
        self.entry_z = ttk.Entry(frame_controls, width=10)
        self.entry_z.insert(0, "")
        self.entry_z.grid(row=0, column=2, padx=5)
        
        self.label_y = ttk.Label(frame_controls, text=self.strings["value_y"])
        self.label_y.grid(row=0, column=3, padx=5)
        self.entry_y = ttk.Entry(frame_controls, width=10)
        self.entry_y.insert(0, "")
        self.entry_y.grid(row=0, column=4, padx=5)
        
        self.checkbox_debug = ttk.Checkbutton(frame_controls, text="Debug", variable=self.debug_var)
        self.checkbox_debug.grid(row=0, column=5, padx=5)
        
        self.btn_generate = ttk.Button(frame_controls, text=self.strings["generate_scheme"], command=self.process_image)
        self.btn_generate.grid(row=0, column=6, padx=5)
        
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
        self.btn_zoom = ttk.Button(frame_actions, text=self.strings["visualize_details"], command=self.zoom_scheme)
        self.btn_zoom.pack(side="left", padx=5)
    
    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Selecione a Imagem",
            filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("Todos os arquivos", "*.*")]
        )
        if file_path:
            try:
                self.image_pil = Image.open(file_path).convert("RGB")
                messagebox.showinfo(self.strings["load_image"], f"{self.strings['load_success']} {file_path}")
            except Exception as e:
                messagebox.showerror(self.strings["error"], f"Erro ao carregar a imagem:\n{e}")
    
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
        else:
            try:
                real_y = float(y_str)
            except ValueError:
                messagebox.showerror(self.strings["error"], "Valor de Y inválido. Informe um número.")
                return
        img_height = self.image_pil.height
        scale = real_z / img_height
        if self.debug_var.get():
            print(f"Escala: {scale:.4f} m/px (Z = {real_z} m; altura = {img_height} px)")
        self.blocks, small_px, new_width, new_height, num_rows, num_cols = generate_blocks_greedy(
            self.image_pil, scale, threshold=30.0, debug=self.debug_var.get())
        if not self.blocks:
            messagebox.showinfo(self.strings["warning"], "Nenhum bloco gerado. Verifique a imagem e os parâmetros.")
            return
        instructions = generate_instructions_from_blocks(self.blocks, small_px, scale, real_y)
        summary = {}
        for inst in instructions:
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
    
    def show_preview(self):
        preview_window = tk.Toplevel(self)
        preview_window.title(self.strings["preview_title"])
        # Redimensiona a imagem para caber em um tamanho máximo fixo (400x400)
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
    
    def zoom_scheme(self):
        if self.schematic is None:
            messagebox.showwarning(self.strings["warning"], "Nenhum esquema gerado para visualizar!")
            return
        ZoomWindow(self, self.schematic)

# ===================== Execução Principal =====================
def main():
    root = tk.Tk()
    app = PixelArtSchematicApp(root)
    app.pack(expand=True, fill="both")
    root.mainloop()

if __name__ == "__main__":
    main()
