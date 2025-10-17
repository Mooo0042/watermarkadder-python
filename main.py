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
    # Set TCL/TK library paths to bundled directories
    os.environ['TCL_LIBRARY'] = os.path.join(base_path, 'tcl', 'tcl8.6')
    os.environ['TK_LIBRARY'] = os.path.join(base_path, 'tcl', 'tk8.6')
    print(f"TCL_LIBRARY: {os.environ['TCL_LIBRARY']}")
    print(f"TK_LIBRARY: {os.environ['TK_LIBRARY']}")

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
    if SVG_SUPPORT:
        filetypes = [("Bilddateien", "*.png *.jpg *.jpeg *.bmp *.gif *.svg")]
    else:
        filetypes = [("Bilddateien", "*.png *.jpg *.jpeg *.bmp *.gif")]
    
    pfad = filedialog.askopenfilename(filetypes=filetypes)
    if pfad:
        if pfad.lower().endswith(".svg") and not SVG_SUPPORT:
            messagebox.showerror("Fehler", "SVG-Unterstützung ist nicht verfügbar. Bitte verwenden Sie PNG, JPG oder andere Bildformate.")
            return
        var.set(pfad)

def logo_bild_laden(pfad):
    if not pfad or not os.path.exists(pfad):
        return None
    try:
        if pfad.lower().endswith(".svg"):
            if not SVG_SUPPORT:
                messagebox.showerror("Fehler", "SVG-Unterstützung ist nicht verfügbar. Bitte verwenden Sie PNG, JPG oder andere Bildformate.")
                return None
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
        deckkraft_regler.get(),
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
        preview_label.image = tk_img  # fix: keep reference alive
        preview_label.pack()

        nav_frame = tk.Frame(preview_window)
        nav_frame.pack(pady=10)
        tk.Button(nav_frame, text="Zurück", command=lambda: zeige_vorschau(-1)).pack(side="left", padx=5)
        tk.Button(nav_frame, text="Weiter", command=lambda: zeige_vorschau(1)).pack(side="left", padx=5)
    else:
        preview_window.title(f"Vorschau: {bild_name}")
        preview_label.configure(image=tk_img)
        preview_label.image = tk_img  # fix: keep reference alive

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
            deckkraft_regler.get(),
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