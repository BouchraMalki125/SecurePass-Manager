import tkinter as tk
from tkinter import ttk, simpledialog
import sqlite3
import base64
import time

# --- PALETTE DE COULEURS : NAVY & WHITE (Style Professionnel) ---
C_BG = "#F4F7F6"        # Blanc cassé / Gris très doux (Fond principal)
C_SURFACE = "#FFFFFF"   # Blanc pur (Cartes/Listes)
C_ACCENT = "#003366"    # Navy Blue (Bleu Marine profond)
C_ACCENT_HOVER = "#004080" # Bleu un peu plus clair pour le survol
C_ERROR = "#B00020"     # Rouge foncé
C_TEXT = "#001F3F"      # Bleu très sombre (presque noir) pour le texte
C_TEXT_SEC = "#546E7A"  # Gris Bleu pour les sous-titres
C_INPUT_BG = "#E8ECEF"  # Gris très clair pour les champs de saisie
C_BORDER = "#CFD8DC"    # Gris bleuté pour les bordures

# --- POLICES (Propre et Corporate) ---
FONT_H1 = ("Helvetica", 24, "bold")
FONT_BODY = ("Helvetica", 11)
FONT_BTN = ("Helvetica", 11, "bold")
FONT_SMALL = ("Helvetica", 9)

MASTER_PASSWORD = "1234"

# --- COUCHE DONNÉES (SQLITE - Inchangée) ---
class DatabaseManager:
    def __init__(self, db_name="securepass.db"):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute("""CREATE TABLE IF NOT EXISTS credentials (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service TEXT NOT NULL, email TEXT NOT NULL, password TEXT NOT NULL)""")
        conn.commit(); conn.close()

    def _encrypt(self, text): return base64.b64encode(text.encode()).decode()
    def _decrypt(self, text): return base64.b64decode(text.encode()).decode()

    def add_entry(self, s, e, p):
        try:
            conn = sqlite3.connect(self.db_name)
            conn.execute("INSERT INTO credentials (service, email, password) VALUES (?, ?, ?)",
                         (self._encrypt(s), self._encrypt(e), self._encrypt(p)))
            conn.commit(); conn.close()
            return True
        except: return False

    def get_all_entries(self):
        conn = sqlite3.connect(self.db_name)
        cur = conn.cursor()
        cur.execute("SELECT id, service, email, password FROM credentials")
        data = [(r[0], self._decrypt(r[1]), self._decrypt(r[2]), self._decrypt(r[3])) for r in cur.fetchall()]
        conn.close()
        return data

# --- COMPOSANTS UI ANIMÉS (Adaptés au thème clair) ---

class ToastNotification:
    def __init__(self, master):
        self.master = master
        # Le toast reste sombre pour le contraste
        self.frame = tk.Frame(master, bg=C_ACCENT, padx=20, pady=15)
        self.label = tk.Label(self.frame, text="", bg=C_ACCENT, fg="white", font=FONT_BODY)
        self.label.pack()
        self.is_visible = False

    def show(self, message, is_error=False):
        if self.is_visible: return 
        
        color = C_ERROR if is_error else C_ACCENT
        self.frame.config(bg=color)
        self.label.config(text=message, bg=color)
        
        self.frame.place(relx=0.5, rely=1.0, anchor="s", y=100, relwidth=0.9)
        self.frame.lift()
        self.is_visible = True
        self.animate_up(80) # On le remonte un peu plus haut

    def animate_up(self, offset):
        if offset > -30: 
            offset -= 8
            self.frame.place(relx=0.5, rely=1.0, anchor="s", y=offset)
            self.master.after(10, lambda: self.animate_up(offset))
        else:
            self.master.after(2500, lambda: self.animate_down(-30))

    def animate_down(self, offset):
        if offset < 100:
            offset += 5 
            self.frame.place(relx=0.5, rely=1.0, anchor="s", y=offset)
            self.master.after(10, lambda: self.animate_down(offset))
        else:
            self.frame.place_forget()
            self.is_visible = False

class ModernEntry(tk.Frame):
    def __init__(self, parent, label_text, is_password=False, with_eye=False):
        super().__init__(parent, bg=C_BG)
        self.pack(fill="x", pady=12)
        
        # Label (Couleur sombre maintenant)
        tk.Label(self, text=label_text, bg=C_BG, fg=C_TEXT_SEC, font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        # Container input (Gris clair)
        self.input_frame = tk.Frame(self, bg=C_INPUT_BG, padx=5, pady=5)
        self.input_frame.pack(fill="x")

        # Entry (Fond gris clair, Texte sombre)
        self.entry = tk.Entry(self.input_frame, bg=C_INPUT_BG, fg=C_TEXT, font=FONT_BODY, 
                              relief="flat", insertbackground=C_ACCENT) # Curseur bleu
        if is_password: self.entry.config(show="•")
        self.entry.pack(side="left", fill="x", expand=True, padx=5)

        if with_eye:
            self.eye_btn = tk.Button(self.input_frame, text="👁️", bg=C_INPUT_BG, fg=C_TEXT_SEC, 
                                     relief="flat", cursor="hand2", command=self.toggle_eye, bd=0)
            self.eye_btn.pack(side="right", padx=5)
        
        # La barre animée (Bleu Marine)
        self.line = tk.Frame(self, bg=C_BORDER, height=2)
        self.line.pack(fill="x")

        self.entry.bind("<FocusIn>", self.on_focus)
        self.entry.bind("<FocusOut>", self.on_unfocus)

    def toggle_eye(self):
        if self.entry.cget('show') == '':
            self.entry.config(show='•')
            self.eye_btn.config(text="👁️")
        else:
            self.entry.config(show='')
            self.eye_btn.config(text="🔒")

    def on_focus(self, e):
        self.line.config(bg=C_ACCENT, height=2)

    def on_unfocus(self, e):
        self.line.config(bg=C_BORDER, height=1)

    def get(self): return self.entry.get()
    def delete(self, f, l): self.entry.delete(f, l)

class MotionButton(tk.Button):
    def __init__(self, master, text, command, primary=True):
        # Primary: Navy fond, Blanc texte
        # Secondary: Blanc fond, Navy texte (+ bordure implicite)
        bg = C_ACCENT if primary else C_SURFACE
        fg = "white" if primary else C_ACCENT
        
        super().__init__(master, text=text, command=command, bg=bg, fg=fg, 
                         font=FONT_BTN, relief="flat", cursor="hand2", padx=20, pady=12, bd=0)
        
        self.primary = primary
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        if self.primary:
            self.config(bg=C_ACCENT_HOVER)
        else:
            self.config(bg="#E3F2FD") # Bleu très très pâle au survol du bouton secondaire

    def on_leave(self, e):
        bg = C_ACCENT if self.primary else C_SURFACE
        self.config(bg=bg)


# --- APPLICATION PRINCIPALE ---
class SecurePassApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SecurePass Pro")
        self.root.geometry("450x750")
        self.root.configure(bg=C_BG)
        self.root.resizable(False, False)

        self.db = DatabaseManager()
        self.toast = ToastNotification(root)
        
        self.show_passwords = False
        self.passwords_map = {}
        
        self.container = tk.Frame(root, bg=C_BG)
        self.container.pack(fill="both", expand=True)
        
        # Styles Treeview pour fond CLAIR
        style = ttk.Style()
        style.theme_use('clam')
        
        # Liste: Fond blanc, texte bleu sombre
        style.configure("Treeview", 
                        background=C_SURFACE, 
                        foreground=C_TEXT, 
                        fieldbackground=C_SURFACE, 
                        borderwidth=0, 
                        rowheight=45,
                        font=FONT_BODY)
        
        # En-têtes: Fond gris clair, texte gras
        style.configure("Treeview.Heading", 
                        background=C_INPUT_BG, 
                        foreground=C_TEXT, 
                        borderwidth=0, 
                        font=("Helvetica", 10, "bold"))
        
        # Sélection: Fond Navy, Texte blanc
        style.map("Treeview", 
                  background=[('selected', C_ACCENT)], 
                  foreground=[('selected', 'white')])

        self.current_frame = None
        self.show_dashboard(animate=False)

    # --- NAVIGATION (Inchangée) ---
    def navigate(self, page_func, direction="forward"):
        new_frame = page_func(self.container)
        width = 450
        start_x = width if direction == "forward" else -width
        
        if self.current_frame:
            self.animate_slide(self.current_frame, new_frame, start_x, 0, direction)
        else:
            new_frame.place(x=0, y=0, relwidth=1, relheight=1)
            self.current_frame = new_frame

    def animate_slide(self, old_f, new_f, new_x, target_x, direction):
        step = 45
        new_f.place(x=new_x, y=0, relwidth=1, relheight=1)
        
        def _step():
            nonlocal new_x
            current_old_x = int(old_f.place_info()['x'])
            
            if direction == "forward":
                new_x -= step
                old_x_new = current_old_x - step
                cond = new_x > target_x
            else:
                new_x += step
                old_x_new = current_old_x + step
                cond = new_x < target_x

            if cond:
                new_f.place(x=new_x, y=0)
                old_f.place(x=old_x_new, y=0)
                self.root.after(10, _step)
            else:
                old_f.destroy()
                new_f.place(x=0, y=0)
                self.current_frame = new_f
        _step()

    # --- PAGES ---

    def create_dashboard(self, parent):
        frame = tk.Frame(parent, bg=C_BG)
        
        # Header
        header = tk.Frame(frame, bg=C_BG, pady=25, padx=25)
        header.pack(fill="x")
        
        # Titre Navy
        tk.Label(header, text="Mon Coffre", bg=C_BG, fg=C_ACCENT, font=FONT_H1).pack(side="left")
        
        # Bouton "+" Rond (Navy)
        btn_add = tk.Button(header, text="+", bg=C_ACCENT, fg="white", font=("Arial", 14, "bold"),
                            relief="flat", cursor="hand2", width=3, bd=0,
                            command=lambda: self.navigate(self.create_add_page, "forward"))
        btn_add.pack(side="right")

        # Liste
        list_container = tk.Frame(frame, bg=C_BG, padx=15)
        list_container.pack(fill="both", expand=True)
        
        # Cadre blanc pour la liste (effet carte)
        card_frame = tk.Frame(list_container, bg=C_SURFACE, bd=1, relief="solid") # petite bordure
        card_frame.config(highlightbackground=C_BORDER, highlightthickness=1)
        card_frame.pack(fill="both", expand=True)

        cols = ("service", "pwd")
        self.tree = ttk.Treeview(card_frame, columns=cols, show="headings", style="Treeview")
        self.tree.heading("service", text="   SERVICE / COMPTE", anchor="w")
        self.tree.heading("pwd", text="MOT DE PASSE", anchor="w")
        self.tree.column("service", width=250)
        self.tree.column("pwd", width=150)
        self.tree.pack(fill="both", expand=True, padx=2, pady=2)

        # Bottom Bar
        bar = tk.Frame(frame, bg=C_BG, height=80, pady=15)
        bar.pack(fill="x", side="bottom")
        
        self.btn_eye = MotionButton(bar, text="👁️", command=self.toggle_visibility, primary=False)
        self.btn_eye.pack(side="left", padx=25)
        
        MotionButton(bar, text="Copier le MDP", command=self.copy_pwd, primary=True).pack(side="right", padx=25)

        self.load_data()
        return frame

    def create_add_page(self, parent):
        frame = tk.Frame(parent, bg=C_BG)
        
        # Header
        tk.Label(frame, text="Ajouter un compte", bg=C_BG, fg=C_ACCENT, font=FONT_H1).pack(pady=(40, 20))
        
        form = tk.Frame(frame, bg=C_BG, padx=35)
        form.pack(fill="x")

        self.inp_service = ModernEntry(form, "Nom du Service (ex: Google)")
        self.inp_email = ModernEntry(form, "Email ou Identifiant")
        self.inp_pwd = ModernEntry(form, "Mot de Passe", is_password=True, with_eye=True)

        btn_box = tk.Frame(frame, bg=C_BG, pady=50)
        btn_box.pack(fill="x", padx=35)
        
        MotionButton(btn_box, text="Annuler", command=lambda: self.navigate(self.create_dashboard, "backward"), primary=False).pack(side="left")
        MotionButton(btn_box, text="Enregistrer", command=self.save_data, primary=True).pack(side="right")

        return frame

    # --- LOGIQUE ---
    
    def show_dashboard(self, animate=True):
        if animate: self.navigate(self.create_dashboard, "backward")
        else:
            f = self.create_dashboard(self.container)
            f.place(x=0, y=0, relwidth=1, relheight=1)
            self.current_frame = f

    def save_data(self):
        s, e, p = self.inp_service.get(), self.inp_email.get(), self.inp_pwd.get()
        if s and p:
            if self.db.add_entry(s, e, p):
                self.toast.show("Compte ajouté avec succès")
                self.navigate(self.create_dashboard, "backward")
            else:
                self.toast.show("Erreur Base de Données", True)
        else:
            self.toast.show("Veuillez remplir les champs", True)

    def load_data(self):
        self.tree.delete(*self.tree.get_children())
        self.passwords_map = {}
        for r in self.db.get_all_entries():
            display_service = f"   {r[1]} \n   {r[2]}" # Indentation pour le style
            display_pwd = r[3] if self.show_passwords else "•••• ••••"
            iid = self.tree.insert("", "end", values=(display_service, display_pwd))
            self.passwords_map[iid] = r[3]

    def toggle_visibility(self):
        if not self.show_passwords:
            pwd = simpledialog.askstring("Sécurité", "Code PIN (1234):", show="*", parent=self.root)
            if pwd == MASTER_PASSWORD:
                self.show_passwords = True
                self.btn_eye.config(text="🔒 Masquer", fg="white", bg=C_ACCENT)
                self.load_data()
                self.toast.show("Mots de passe visibles")
            elif pwd:
                self.toast.show("Code incorrect", True)
        else:
            self.show_passwords = False
            self.btn_eye.config(text="👁️", fg=C_ACCENT, bg=C_SURFACE)
            self.load_data()

    def copy_pwd(self):
        sel = self.tree.selection()
        if sel:
            pwd = simpledialog.askstring("Sécurité", "Code PIN pour copier:", show="*", parent=self.root)
            if pwd == MASTER_PASSWORD:
                real = self.passwords_map.get(sel[0])
                self.root.clipboard_clear(); self.root.clipboard_append(real)
                self.toast.show("Copié dans le presse-papier !")
            else:
                self.toast.show("Code incorrect", True)
        else:
            self.toast.show("Sélectionnez un compte", True)

if __name__ == "__main__":
    root = tk.Tk()
    app = SecurePassApp(root)
    root.mainloop()