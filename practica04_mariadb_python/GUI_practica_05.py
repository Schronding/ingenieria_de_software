import tkinter as tk
from tkinter import ttk, messagebox
import mariadb
import os
from dotenv import load_dotenv

# Se inserto en la base de datos de forma correcta la siguiente informacion:

# --- AUTOR --- 
# ID: 17	NOMBRE: Donna Louise Tartt	FINADO: 0	FECHA_DE_NACIMIENTO: 1963-12-23	BIOGRAFIA: Donna Louise Tartt (1963) es una aclamada escritora estadounidense de Mississippi, celebrada por su 
# producción literaria escasa pero de gran impacto. Es conocida por su meticuloso y lento proceso de escritura, lo que explica los largos períodos entre 
# cada una de sus novelas.
# --- AUTOR --- 

# --- EDITORIAL --- 
# ID: 6	NOMBRE: Penguin Random House Grupo Editorial	UBICACION: Barcelona, España
# --- EDITORIAL ---

# --- GENERO ---
# ID: 6	NOMBRE: Academia Oscura	POPULARIDAD: 88	DESCRIPCION: Subgénero de ficción ambientado en un entorno académico elitista. Explora la obsesión por el conocimiento, la estética clásica y 
# a moralidad ambigua, a menudo en torno a un crimen o una tragedia.
# --- GENERO ---

# --- LIBRO ---
# ISBN: 978-84-264-2021-2	NOMBRE: El Secreto	PRECIO: 650.00	CANTIDAD: 14	ID_EDITORIAL: 6
# --- LIBRO ---


def get_db_connection():
    load_dotenv()
    try:
        conn = mariadb.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")),
            database=os.getenv("DB_NAME")
        )
        return conn
    except mariadb.Error as e:
        messagebox.showerror("Error de Conexión", f"No se pudo conectar a la base de datos: {e}")
        return None

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestor de Inserciones - Librería")
        self.geometry("500x400")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        self.create_editorial_tab()
        self.create_genero_tab()
        self.create_autor_tab()
        self.create_libro_tab()

    def create_editorial_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Editoriales")

        ttk.Label(tab, text="Nombre:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        nombre_entry = ttk.Entry(tab, width=40)
        nombre_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(tab, text="Ubicación:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ubicacion_entry = ttk.Entry(tab, width=40)
        ubicacion_entry.grid(row=1, column=1, padx=5, pady=5)

        insert_button = ttk.Button(tab, text="Insertar Editorial", 
                                   command=lambda: self.insert_editorial(nombre_entry, ubicacion_entry))
        insert_button.grid(row=2, column=0, columnspan=2, pady=15)

    def insert_editorial(self, nombre_entry, ubicacion_entry):
        nombre = nombre_entry.get()
        ubicacion = ubicacion_entry.get()

        if not nombre:
            messagebox.showwarning("Campo Vacío", "El nombre de la editorial no puede estar vacío.")
            return

        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()

        try:
            query = "INSERT INTO editorial (E_nombre, E_ubicacion) VALUES (?, ?)"
            cursor.execute(query, (nombre, ubicacion))
            conn.commit()
            messagebox.showinfo("Éxito", "Editorial insertada correctamente.")
            nombre_entry.delete(0, tk.END)
            ubicacion_entry.delete(0, tk.END)
        except mariadb.Error as e:
            messagebox.showerror("Error en Inserción", f"No se pudo insertar la editorial: {e}")
        finally:
            conn.close()

    def create_genero_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Géneros")

        ttk.Label(tab, text="Nombre:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        nombre_entry = ttk.Entry(tab, width=40)
        nombre_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(tab, text="Popularidad:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        popularidad_entry = ttk.Entry(tab, width=40)
        popularidad_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(tab, text="Descripción:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        descripcion_entry = tk.Text(tab, width=30, height=5)
        descripcion_entry.grid(row=2, column=1, padx=5, pady=5)

        insert_button = ttk.Button(tab, text="Insertar Género",
                                   command=lambda: self.insert_genero(nombre_entry, popularidad_entry, descripcion_entry))
        insert_button.grid(row=3, column=0, columnspan=2, pady=15)

    def insert_genero(self, nombre_entry, popularidad_entry, descripcion_entry):
        nombre = nombre_entry.get()
        popularidad = popularidad_entry.get()
        descripcion = descripcion_entry.get("1.0", tk.END).strip()

        if not nombre:
            messagebox.showwarning("Campo Vacío", "El nombre del género no puede estar vacío.")
            return
        
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()

        try:
            query = "INSERT INTO genero (G_nombre, G_popularidad, G_descripcion) VALUES (?, ?, ?)"
            cursor.execute(query, (nombre, int(popularidad) if popularidad else 0, descripcion))
            conn.commit()
            messagebox.showinfo("Éxito", "Género insertado correctamente.")
            nombre_entry.delete(0, tk.END)
            popularidad_entry.delete(0, tk.END)
            descripcion_entry.delete("1.0", tk.END)
        except mariadb.Error as e:
            messagebox.showerror("Error en Inserción", f"No se pudo insertar el género: {e}")
        except ValueError:
            messagebox.showerror("Error de Formato", "La popularidad debe ser un número entero.")
        finally:
            conn.close()
    
    def create_autor_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Autores")

        ttk.Label(tab, text="Nombre:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.autor_nombre = ttk.Entry(tab, width=40)
        self.autor_nombre.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(tab, text="Fecha Nacimiento (AAAA-MM-DD):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.autor_fecha = ttk.Entry(tab, width=40)
        self.autor_fecha.grid(row=1, column=1, padx=5, pady=5)

        self.autor_finado = tk.BooleanVar()
        ttk.Checkbutton(tab, text="¿Finado?", variable=self.autor_finado).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(tab, text="Biografía:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.autor_bio = tk.Text(tab, width=30, height=5)
        self.autor_bio.grid(row=3, column=1, padx=5, pady=5)

        insert_button = ttk.Button(tab, text="Insertar Autor", command=self.insert_autor)
        insert_button.grid(row=4, column=0, columnspan=2, pady=15)
        
    def insert_autor(self):
        nombre = self.autor_nombre.get()
        fecha_nac = self.autor_fecha.get() 
        finado = self.autor_finado.get()
        biografia = self.autor_bio.get("1.0", tk.END).strip()

        if not nombre:
            messagebox.showwarning("Campo Vacío", "El nombre del autor no puede estar vacío.")
            return

        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()

        try:
            query = "INSERT INTO autor (A_nombre, A_finado, A_fecha_n, A_biografia) VALUES (?, ?, ?, ?)"
            cursor.execute(query, (nombre, finado, fecha_nac, biografia))
            conn.commit()
            messagebox.showinfo("Éxito", "Autor insertado correctamente.")
            self.autor_nombre.delete(0, tk.END)
            self.autor_fecha.delete(0, tk.END)
            self.autor_bio.delete("1.0", tk.END)
            self.autor_finado.set(False)
        except mariadb.Error as e:
            messagebox.showerror("Error en Inserción", f"No se pudo insertar el autor: {e}")
        finally:
            conn.close()

    def create_libro_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Libros")

        ttk.Label(tab, text="ISBN:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.libro_isbn = ttk.Entry(tab, width=40)
        self.libro_isbn.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(tab, text="Nombre:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.libro_nombre = ttk.Entry(tab, width=40)
        self.libro_nombre.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(tab, text="Precio:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.libro_precio = ttk.Entry(tab, width=40)
        self.libro_precio.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(tab, text="Cantidad:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.libro_cantidad = ttk.Entry(tab, width=40)
        self.libro_cantidad.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(tab, text="Editorial:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.libro_editorial = ttk.Combobox(tab, width=38)
        self.libro_editorial.grid(row=4, column=1, padx=5, pady=5)
        
        self.load_editoriales()

        insert_button = ttk.Button(tab, text="Insertar Libro", command=self.insert_libro)
        insert_button.grid(row=5, column=0, columnspan=2, pady=15)

    def load_editoriales(self):
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        self.editoriales_map = {}
        try:
            cursor.execute("SELECT ID_editorial, E_nombre FROM editorial")
            editoriales = cursor.fetchall()
            for id_ed, nombre_ed in editoriales:
                self.editoriales_map[nombre_ed] = id_ed
            self.libro_editorial['values'] = list(self.editoriales_map.keys())
        except mariadb.Error as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar las editoriales: {e}")
        finally:
            conn.close()

    def insert_libro(self):
        isbn = self.libro_isbn.get()
        nombre = self.libro_nombre.get()
        precio = self.libro_precio.get()
        cantidad = self.libro_cantidad.get()
        editorial_nombre = self.libro_editorial.get()

        if not all([isbn, nombre, precio, cantidad, editorial_nombre]):
            messagebox.showwarning("Campos Vacíos", "Todos los campos son obligatorios.")
            return

        editorial_id = self.editoriales_map.get(editorial_nombre)
        
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()

        try:
            query = "INSERT INTO libro (L_ISBN, L_nombre, L_Precio, L_Cantidad, ID_editorial) VALUES (?, ?, ?, ?, ?)"
            cursor.execute(query, (isbn, nombre, float(precio), int(cantidad), editorial_id))
            conn.commit()
            messagebox.showinfo("Éxito", "Libro insertado correctamente.")
            self.libro_isbn.delete(0, tk.END)
            self.libro_nombre.delete(0, tk.END)
            self.libro_precio.delete(0, tk.END)
            self.libro_cantidad.delete(0, tk.END)
            self.libro_editorial.set('')
        except mariadb.Error as e:
            messagebox.showerror("Error de Inserción", f"No se pudo insertar el libro: {e}")
        except ValueError:
            messagebox.showerror("Error de Formato", "Precio y cantidad deben ser números válidos.")
        finally:
            conn.close()


if __name__ == "__main__":
    app = App()
    app.mainloop()