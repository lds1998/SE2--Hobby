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
        "dark": "Dark",
        "exclude_blocks": "Incluir blocos:",
        "include_25": "25 cm",
        "include_50": "50 cm",
        "include_2_5": "2.5 m",
        "thickness_3d": "Considerar espessura 3D",
        "edge_pref": "Preferência para borda:",
        "interior_pref": "Preferência para interior:",
        "use_pref": "Utilizar preferências de borda/interior"
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
        "dark": "Dark",
        "exclude_blocks": "Include blocks:",
        "include_25": "25 cm",
        "include_50": "50 cm",
        "include_2_5": "2.5 m",
        "thickness_3d": "Consider 3D thickness",
        "edge_pref": "Edge preference:",
        "interior_pref": "Interior preference:",
        "use_pref": "Use edge/interior preferences"
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
    """Converte a imagem para escala de cinza e retorna uma máscara booleana."""
    gray = image.convert("L")
    arr = np.array(gray)
    mask = arr < shape_thresh
    return mask

def generate_blocks_with_allowed(image_pil, scale, allowed_types, threshold=30.0, debug=False):
    """
    Gera blocos usando somente os tipos permitidos (allowed_types).
    Cada tipo é mapeado para um tamanho: "25cm" → 1 célula, "50cm" → 2 células, "2.5m" → 10 células.
    Tenta mesclar células para os tipos permitidos (maior primeiro).
    Preenche as células restantes com o tipo fallback, SE HOUVER ALGO PERMITIDO.
    Se allowed_types estiver vazio, retorna uma lista vazia.
    Retorna: blocks, small_px, new_width, new_height, num_rows, num_cols, inside.
    """
    size_mapping = {"25cm": 1, "50cm": 2, "2.5m": 10}
    if not allowed_types:
        if debug:
            print("Nenhum tipo de bloco permitido. Retornando lista vazia.")
        # Retorna a matriz 'inside' mesmo que não haja blocos
        width, height = image_pil.size
        small_px = int(round(0.25 / scale))
        if small_px <= 0:
            small_px = 1
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
        return [], small_px, new_width, new_height, num_rows, num_cols, inside

    allowed_order = sorted(allowed_types, key=lambda t: size_mapping[t], reverse=True)
    # Define fallback: o menor dos tipos permitidos
    fallback = min(allowed_types, key=lambda t: size_mapping[t])
    
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
    
    # Tenta mesclar para cada tipo permitido (maior primeiro)
    for t in allowed_order:
        bs = size_mapping[t]
        for r in range(num_rows - bs + 1):
            for c in range(num_cols - bs + 1):
                if not np.all(inside[r:r+bs, c:c+bs]):
                    continue
                if np.any(merged[r:r+bs, c:c+bs]):
                    continue
                region = cell_colors[r:r+bs, c:c+bs]
                avg = region.mean(axis=(0,1))
                diff = np.abs(region - avg)
                if diff.max() <= threshold:
                    merged[r:r+bs, c:c+bs] = True
                    blocks.append({
                        "row_start": r,
                        "col_start": c,
                        "cell_size": bs,
                        "avg_color": avg,
                        "block_type": t
                    })
    # Preenche as células restantes com o fallback (se houver)
    for r in range(num_rows):
        for c in range(num_cols):
            if inside[r, c] and not merged[r, c]:
                merged[r, c] = True
                bs = size_mapping[fallback]
                blocks.append({
                    "row_start": r,
                    "col_start": c,
                    "cell_size": bs,
                    "avg_color": cell_colors[r, c],
                    "block_type": fallback
                })
    if debug:
        total_cells = num_rows * num_cols
        print(f"Total de células: {total_cells}, Blocos gerados: {len(blocks)}")
    return blocks, small_px, new_width, new_height, num_rows, num_cols, inside

def generate_instructions_from_blocks(blocks, small_px, scale, constant_y, use_3d=False):
    """
    Gera instruções de posicionamento a partir dos blocos detectados.
    blocks: lista de dicionários de blocos.
    small_px: tamanho da menor célula em pixels.
    scale: fator de conversão de pixels para metros.
    constant_y: valor Y aplicado a todas as instruções.
    use_3d: considera espessuras padrão ao calcular a altura.

    Retorna uma lista de dicionários com as chaves
    'block_type', 'x', 'y', 'z', 'width' e 'height'.
    """
    default_thickness = {"25cm": 0.25, "50cm": 0.50, "2.5m": 2.50}
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
        if use_3d:
            h_val = default_thickness.get(block["block_type"], round(height_px * scale, 2))
        else:
            h_val = round(height_px * scale, 2)
        instructions.append({
            "block_type": block["block_type"],
            "x": round(center_x, 2),
            "y": constant_y,
            "z": round(center_z, 2),
            "width": round(width_px * scale, 2),
            "height": h_val
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
        self.lbl_exclude.config(text=self.strings["exclude_blocks"])
        self.cb_edge_label.config(text=self.strings["edge_pref"])
        self.cb_interior_label.config(text=self.strings["interior_pref"])
        self.cb_use_pref_label.config(text=self.strings["use_pref"])
        self.cb_thickness_label.config(text=self.strings["thickness_3d"])
    
    def create_widgets(self):
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
        
        # Opções extras
        frame_extras = ttk.Frame(self)
        frame_extras.pack(pady=10, fill="x", padx=10)
        self.lbl_exclude = ttk.Label(frame_extras, text=self.strings["exclude_blocks"])
        self.lbl_exclude.grid(row=0, column=0, padx=5)
        self.include_25_var = tk.BooleanVar(value=True)
        self.include_50_var = tk.BooleanVar(value=True)
        self.include_2_5_var = tk.BooleanVar(value=True)
        self.cb_include_25 = ttk.Checkbutton(frame_extras, text=self.strings["include_25"], variable=self.include_25_var)
        self.cb_include_25.grid(row=0, column=1, padx=5)
        self.cb_include_50 = ttk.Checkbutton(frame_extras, text=self.strings["include_50"], variable=self.include_50_var)
        self.cb_include_50.grid(row=0, column=2, padx=5)
        self.cb_include_2_5 = ttk.Checkbutton(frame_extras, text=self.strings["include_2_5"], variable=self.include_2_5_var)
        self.cb_include_2_5.grid(row=0, column=3, padx=5)
        
        self.cb_3d_var = tk.BooleanVar(value=False)
        self.cb_3d = ttk.Checkbutton(frame_extras, text=self.strings["thickness_3d"], variable=self.cb_3d_var)
        self.cb_3d.grid(row=1, column=0, padx=5, pady=5)
        
        self.cb_edge_label = ttk.Label(frame_extras, text=self.strings["edge_pref"])
        self.cb_edge_label.grid(row=2, column=0, padx=5, pady=5)
        self.combo_edge = ttk.Combobox(frame_extras, values=["2.5m", "50cm", "25cm"], state="readonly", width=10)
        self.combo_edge.set("2.5m")
        self.combo_edge.grid(row=2, column=1, padx=5)
        
        self.cb_interior_label = ttk.Label(frame_extras, text=self.strings["interior_pref"])
        self.cb_interior_label.grid(row=2, column=2, padx=5, pady=5)
        self.combo_interior = ttk.Combobox(frame_extras, values=["2.5m", "50cm", "25cm"], state="readonly", width=10)
        self.combo_interior.set("50cm")
        self.combo_interior.grid(row=2, column=3, padx=5)
        
        self.cb_use_pref_var = tk.BooleanVar(value=False)
        self.cb_use_pref_label = ttk.Label(frame_extras, text=self.strings["use_pref"])
        self.cb_use_pref_label.grid(row=3, column=0, padx=5, pady=5)
        self.cb_use_pref = ttk.Checkbutton(frame_extras, variable=self.cb_use_pref_var)
        self.cb_use_pref.grid(row=3, column=1, padx=5)
        
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
        
        # Define os tipos permitidos com base nos checkbuttons.
        allowed = []
        if self.include_25_var.get():
            allowed.append("25cm")
        if self.include_50_var.get():
            allowed.append("50cm")
        if self.include_2_5_var.get():
            allowed.append("2.5m")
        # Se nenhum tipo for permitido, NÃO usamos fallback – retornamos blocos vazios.
        
        # Gera os blocos usando somente os tipos permitidos.
        self.blocks, small_px, new_width, new_height, num_cols, num_rows, inside = generate_blocks_with_allowed(
            self.image_pil, scale, allowed, threshold=30.0, debug=self.debug_var.get())
        if not self.blocks:
            messagebox.showinfo(self.strings["warning"], "Nenhum bloco gerado (possivelmente nenhum tipo permitido).")
            return
        
        # Se o toggle de preferências estiver ativo, aplica as preferências para borda/interior.
        if self.cb_use_pref_var.get():
            def is_edge_block(block):
                r0 = block["row_start"]
                c0 = block["col_start"]
                size = block["cell_size"]
                if r0 == 0 or c0 == 0 or (r0 + size) >= num_rows or (c0 + size) >= num_rows:
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
        # Se o toggle não estiver ativo, os blocos já estão dentro dos tipos permitidos.
        
        instructions = generate_instructions_from_blocks(self.blocks, small_px, scale, real_y, use_3d=self.cb_3d_var.get())
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
