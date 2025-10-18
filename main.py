import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageEnhance, ImageStat
import cairosvg
from io import BytesIO

# Windows DPI scaling fix
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# PyInstaller TCL/TK path fix (for Windows onefile builds)
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    print(f"Running as frozen exe")
    print(f"Base path (_MEIPASS): {base_path}")
    
    # Try to find TCL/TK in various possible locations
    tcl_possible = [
        os.path.join(base_path, 'tcl', 'tcl8.6'),
        os.path.join(base_path, 'tcl8.6'),
        os.path.join(base_path, 'tcl', 'tcl8'),
        os.path.join(base_path, 'tcl8'),
    ]
    
    tk_possible = [
        os.path.join(base_path, 'tcl', 'tk8.6'),
        os.path.join(base_path, 'tk8.6'),
        os.path.join(base_path, 'tcl', 'tk8'),
        os.path.join(base_path, 'tk8'),
    ]
    
    # Find actual TCL location
    tcl_found = None
    for path in tcl_possible:
        if os.path.exists(path):
            tcl_found = path
            print(f"Found TCL at: {path}")
            break
    
    # Find actual TK location
    tk_found = None
    for path in tk_possible:
        if os.path.exists(path):
            tk_found = path
            print(f"Found TK at: {path}")
            break
    
    if tcl_found:
        os.environ['TCL_LIBRARY'] = tcl_found
    else:
        print("WARNING: TCL library not found!")
        print(f"Contents of {base_path}:")
        try:
            for item in os.listdir(base_path):
                print(f"  - {item}")
        except Exception as e:
            print(f"  Could not list: {e}")
    
    if tk_found:
        os.environ['TK_LIBRARY'] = tk_found
    else:
        print("WARNING: TK library not found!")
    
    print(f"TCL_LIBRARY set to: {os.environ.get('TCL_LIBRARY', 'NOT SET')}")
    print(f"TK_LIBRARY set to: {os.environ.get('TK_LIBRARY', 'NOT SET')}")
else:
    print("Running in normal Python mode")

# Temp dir override for restricted systems
os.environ["TMPDIR"] = os.getcwd()

# Globale Variablen
image_list = []
current_index = 0
preview_window = None
preview_label = None
preview_image_ref = None

def waehle_ordner():
    pfad = filedialog.askdirectory()
    if pfad:
        bilder_ordner.set(pfad)
        lade_bilderliste()
        messagebox.showinfo("Info", f"{len(image_list)} Bilder geladen aus:\n{pfad}")

def lade_bilderliste():
    global image_list
    folder = bilder_ordner.get()
    valid_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif")
    if not os.path.isdir(folder):
        messagebox.showerror("Fehler", "Kein gültiger Ordner ausgewählt!")
        return
    image_list = [f for f in os.listdir(folder) if f.lower().endswith(valid_extensions)]
    if not image_list:
        messagebox.showwarning("Warnung", "Keine Bilder im Ordner gefunden.")

def waehle_logo_datei(var):
    pfad = filedialog.askopenfilename(filetypes=[("Bilddateien", "*.png *.jpg *.jpeg *.bmp *.gif *.svg")])
    if pfad:
        var.set(pfad)

def logo_bild_laden(pfad):
    if not pfad or not os.path.exists(pfad):
        return None
    try:
        if pfad.lower().endswith(".svg"):
            png_data = cairosvg.svg2png(url=pfad)
            img = Image.open(BytesIO(png_data)).convert("RGBA")
        else:
            img = Image.open(pfad).convert("RGBA")
        return img
    except Exception as e:
        messagebox.showerror("Fehler", f"Logo konnte nicht geladen werden:\n{e}")
        return None

def berechne_helligkeit(img):
    grayscale = img.convert("L")
    stat = ImageStat.Stat(grayscale)
    return stat.mean[0]

def berechne_auto_deckkraft(img, min_opacity=30, max_opacity=80):
    helligkeit = berechne_helligkeit(img)
    norm = 1 - (helligkeit / 255)
    opacity = min_opacity + (max_opacity - min_opacity) * norm
    return int(opacity)

def wasserzeichen_auf_bild(img, logo_schwarz, logo_weiss, deckkraft, position, auto_brightness, auto_opacity):
    logo_width = int(img.width * 0.15)
    img_copy = img.copy()

    def prepare_logo(logo):
        if logo is None:
            return None
        ratio = logo_width / logo.width
        return logo.resize((logo_width, int(logo.height * ratio)), Image.LANCZOS)

    logo_s = prepare_logo(logo_schwarz)
    logo_w = prepare_logo(logo_weiss)

    if auto_opacity:
        deckkraft = berechne_auto_deckkraft(img)

    if auto_brightness:
        if logo_s is not None:
            alpha_s = logo_s.split()[3]
            alpha_s = ImageEnhance.Brightness(alpha_s).enhance(deckkraft / 100)
            logo_s.putalpha(alpha_s)
        if logo_w is not None:
            alpha_w = logo_w.split()[3]
            alpha_w = ImageEnhance.Brightness(alpha_w).enhance(deckkraft / 100)
            logo_w.putalpha(alpha_w)
    else:
        if logo_s is not None:
            alpha_s = logo_s.split()[3]
            alpha_s = ImageEnhance.Brightness(alpha_s).enhance(deckkraft / 100)
            logo_s.putalpha(alpha_s)
        logo_w = None

    rand = 20
    basis_logo = logo_s if logo_s is not None else logo_w
    if basis_logo is None:
        return img_copy

    if position == "unten links":
        pos = (rand, img.height - basis_logo.height - rand)
    elif position == "unten rechts":
        pos = (img.width - basis_logo.width - rand, img.height - basis_logo.height - rand)
    elif position == "oben links":
        pos = (rand, rand)
    else:
        pos = (img.width - basis_logo.width - rand, rand)

    offset = (pos[0] + 5, pos[1] + 5)

    if logo_w is not None:
        img_copy.paste(logo_w, offset, logo_w)
    if logo_s is not None:
        img_copy.paste(logo_s, pos, logo_s)

    return img_copy

def zeige_vorschau(index_delta=0):
    global current_index, preview_window, preview_label, preview_image_ref

    if not image_list:
        messagebox.showerror("Fehler", "Bitte zuerst einen Bilder-Ordner auswählen.")
        return

    current_index = (current_index + index_delta) % len(image_list)
    bild_name = image_list[current_index]
    bild_pfad = os.path.join(bilder_ordner.get(), bild_name)

    logo_schwarz_img = logo_bild_laden(logo_datei_schwarz.get())
    logo_weiss_img = logo_bild_laden(logo_datei_weiss.get())
    if logo_schwarz_img is None and logo_weiss_img is None:
        messagebox.showerror("Fehler", "Bitte mindestens ein Logo auswählen.")
        return

    img = Image.open(bild_pfad).convert("RGBA")
    img_preview = wasserzeichen_auf_bild(
        img,
        logo_schwarz_img,
        logo_weiss_img,
        deckkraft_var.get(),  # FIXED: Use deckkraft_var instead of deckkraft_regler
        position_var.get(),
        auto_brightness.get(),
        auto_opacity.get()
    )

    max_w, max_h = 600, 400
    ratio = min(max_w / img_preview.width, max_h / img_preview.height, 1)
    preview_img_resized = img_preview.resize(
        (int(img_preview.width * ratio), int(img_preview.height * ratio)),
        Image.LANCZOS
    )

    tk_img = ImageTk.PhotoImage(preview_img_resized)

    if preview_window is None or not preview_window.winfo_exists():
        preview_window = tk.Toplevel(root)
        preview_window.title(f"Vorschau: {bild_name}")

        preview_label = tk.Label(preview_window, image=tk_img)
        preview_label.image = tk_img
        preview_label.pack()

        nav_frame = tk.Frame(preview_window)
        nav_frame.pack(pady=10)
        tk.Button(nav_frame, text="Zurück", command=lambda: zeige_vorschau(-1)).pack(side="left", padx=5)
        tk.Button(nav_frame, text="Weiter", command=lambda: zeige_vorschau(1)).pack(side="left", padx=5)
    else:
        preview_window.title(f"Vorschau: {bild_name}")
        preview_label.configure(image=tk_img)
        preview_label.image = tk_img

    preview_image_ref = tk_img

def start_batch_verarbeitung():
    if not image_list:
        messagebox.showerror("Fehler", "Bitte zuerst einen Bilder-Ordner auswählen.")
        return

    logo_schwarz_img = logo_bild_laden(logo_datei_schwarz.get())
    logo_weiss_img = logo_bild_laden(logo_datei_weiss.get())
    if logo_schwarz_img is None and logo_weiss_img is None:
        messagebox.showerror("Fehler", "Bitte mindestens ein Logo auswählen.")
        return

    ziel_ordner = filedialog.askdirectory(title="Zielordner für Wasserzeichen-Bilder wählen")
    if not ziel_ordner:
        return

    if not os.access(ziel_ordner, os.W_OK):
        messagebox.showerror("Fehler", f"Keine Schreibrechte für:\n{ziel_ordner}")
        return

    progress['maximum'] = len(image_list)
    progress['value'] = 0
    root.update_idletasks()

    for i, datei in enumerate(image_list):
        bild_pfad = os.path.join(bilder_ordner.get(), datei)
        img = Image.open(bild_pfad).convert("RGBA")

        wasserzeichen_img = wasserzeichen_auf_bild(
            img,
            logo_schwarz_img,
            logo_weiss_img,
            deckkraft_var.get(),  # FIXED: Use deckkraft_var instead of deckkraft_regler
            position_var.get(),
            auto_brightness.get(),
            auto_opacity.get()
        )

        save_path = os.path.join(ziel_ordner, datei)
        wasserzeichen_img.convert("RGB").save(save_path)

        progress['value'] = i + 1
        root.update_idletasks()

    messagebox.showinfo("Fertig", f"Wasserzeichen wurden hinzugefügt und gespeichert in:\n{ziel_ordner}")
    progress['value'] = 0

# Hauptfenster
try:
    print("Initializing tkinter...")
    root = tk.Tk()
    root.title("Wasserzeichen-Tool")
    print("Tkinter initialized successfully!")
except Exception as e:
    print(f"ERROR initializing tkinter: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")
    sys.exit(1)

# Variables
bilder_ordner = tk.StringVar()
logo_datei_schwarz = tk.StringVar()
logo_datei_weiss = tk.StringVar()
position_var = tk.StringVar(value="unten links")
deckkraft_var = tk.IntVar(value=50)  # FIXED: Renamed from deckkraft_regler to deckkraft_var
auto_brightness = tk.BooleanVar(value=False)
auto_opacity = tk.BooleanVar(value=False)

# GUI Layout
frame_ordner = tk.Frame(root)
frame_ordner.pack(fill="x", padx=10, pady=5)
tk.Label(frame_ordner, text="Bilder-Ordner:").pack(anchor="w")
entry_ordner = tk.Entry(frame_ordner, textvariable=bilder_ordner, width=60)
entry_ordner.pack(side="left", padx=(0, 5))
tk.Button(frame_ordner, text="Ordner wählen", command=waehle_ordner).pack(side="left")

frame_logo = tk.Frame(root)
frame_logo.pack(fill="x", padx=10, pady=5)
tk.Label(frame_logo, text="Schwarzes Logo:").grid(row=0, column=0, sticky="w")
entry_logo_s = tk.Entry(frame_logo, textvariable=logo_datei_schwarz, width=60)
entry_logo_s.grid(row=0, column=1, padx=5)
tk.Button(frame_logo, text="Logo wählen", command=lambda: waehle_logo_datei(logo_datei_schwarz)).grid(row=0, column=2)

tk.Label(frame_logo, text="Weißes Logo:").grid(row=1, column=0, sticky="w")
entry_logo_w = tk.Entry(frame_logo, textvariable=logo_datei_weiss, width=60)
entry_logo_w.grid(row=1, column=1, padx=5)
tk.Button(frame_logo, text="Logo wählen", command=lambda: waehle_logo_datei(logo_datei_weiss)).grid(row=1, column=2)

frame_optionen = tk.Frame(root)
frame_optionen.pack(fill="x", padx=10, pady=5)
tk.Label(frame_optionen, text="Position:").grid(row=0, column=0, sticky="w")
positions = ["unten links", "unten rechts", "oben links", "oben rechts"]
pos_dropdown = ttk.Combobox(frame_optionen, values=positions, textvariable=position_var, state="readonly", width=15)
pos_dropdown.grid(row=0, column=1, sticky="w")

tk.Label(frame_optionen, text="Deckkraft:").grid(row=1, column=0, sticky="w")
deckkraft_slider = tk.Scale(frame_optionen, from_=10, to=100, orient="horizontal", variable=deckkraft_var)
deckkraft_slider.grid(row=1, column=1, sticky="w")

cb_auto_brightness = tk.Checkbutton(frame_optionen, text="Automatische Helligkeit (Subtiles Weiß-Schwarz-Wechsel)", variable=auto_brightness)
cb_auto_brightness.grid(row=2, column=0, columnspan=2, sticky="w")

cb_auto_opacity = tk.Checkbutton(frame_optionen, text="Automatische Deckkraft (immer subtil sichtbar)", variable=auto_opacity)
cb_auto_opacity.grid(row=3, column=0, columnspan=2, sticky="w")

frame_buttons = tk.Frame(root)
frame_buttons.pack(fill="x", padx=10, pady=10)
tk.Button(frame_buttons, text="Vorschau zeigen", command=lambda: zeige_vorschau(0)).pack(side="left", padx=5)
tk.Button(frame_buttons, text="Batch starten", command=start_batch_verarbeitung).pack(side="left", padx=5)

progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress.pack(pady=5, padx=10)

print("Starting main loop...")
try:
    root.mainloop()
except Exception as e:
    print(f"ERROR in main loop: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")
    sys.exit(1)
