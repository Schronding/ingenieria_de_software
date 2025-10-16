import tkinter as tk
from tkinter import ttk, messagebox
import mariadb
import os
from dotenv import load_dotenv

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
        self.geometry("600x650") 

        self.editoriales_map = {}
        self.autores_map = {}
        self.generos_map = {}
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        self.create_editorial_tab()
        self.create_genero_tab()
        self.create_autor_tab()
        self.create_libro_tab()

    def refresh_all_data(self):
        self.load_editoriales()
        self.load_autores()
        self.load_generos()
        print("Datos recargados en la pestaña de Libros.")

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
            self.refresh_all_data() 
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
            self.refresh_all_data() 
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
            self.refresh_all_data() 
        except mariadb.Error as e:
            messagebox.showerror("Error en Inserción", f"No se pudo insertar el autor: {e}")
        finally:
            conn.close()

    def create_libro_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Libros")

        libro_frame = ttk.LabelFrame(tab, text="Datos del Libro")
        libro_frame.pack(fill="x", expand=True, padx=10, pady=5)
        
        ttk.Label(libro_frame, text="ISBN:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.libro_isbn = ttk.Entry(libro_frame, width=40)
        self.libro_isbn.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(libro_frame, text="Nombre:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.libro_nombre = ttk.Entry(libro_frame, width=40)
        self.libro_nombre.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(libro_frame, text="Precio:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.libro_precio = ttk.Entry(libro_frame, width=40)
        self.libro_precio.grid(row=2, column=1, padx=5, pady=2)
        
        ttk.Label(libro_frame, text="Cantidad:").grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.libro_cantidad = ttk.Entry(libro_frame, width=40)
        self.libro_cantidad.grid(row=3, column=1, padx=5, pady=2)
        
        ttk.Label(libro_frame, text="Editorial:").grid(row=4, column=0, padx=5, pady=2, sticky="w")
        self.libro_editorial = ttk.Combobox(libro_frame, width=38, state="readonly")
        self.libro_editorial.grid(row=4, column=1, padx=5, pady=2)
        
        insert_libro_button = ttk.Button(libro_frame, text="1. Insertar Libro", command=self.insert_libro)
        insert_libro_button.grid(row=5, column=0, columnspan=2, pady=10)

        rel_frame = ttk.LabelFrame(tab, text="Asignar Autores y Géneros (después de insertar libro)")
        rel_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ttk.Label(rel_frame, text="Autores (Ctrl+Click para multiselect):").grid(row=0, column=0, padx=5, pady=2, sticky="nw")
        self.autores_listbox = tk.Listbox(rel_frame, selectmode="multiple", exportselection=False, height=5)
        self.autores_listbox.grid(row=1, column=0, padx=5, pady=2)
        
        ttk.Label(rel_frame, text="Géneros (Ctrl+Click para multiselect):").grid(row=0, column=1, padx=5, pady=2, sticky="nw")
        self.generos_listbox = tk.Listbox(rel_frame, selectmode="multiple", exportselection=False, height=5)
        self.generos_listbox.grid(row=1, column=1, padx=5, pady=2)
        
        assign_button = ttk.Button(rel_frame, text="2. Asignar Seleccionados", command=self.assign_autores_generos)
        assign_button.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.refresh_all_data()

    def load_editoriales(self):
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        self.editoriales_map.clear()
        try:
            cursor.execute("SELECT ID_editorial, E_nombre FROM editorial ORDER BY E_nombre")
            editoriales = cursor.fetchall()
            for id_ed, nombre_ed in editoriales:
                self.editoriales_map[nombre_ed] = id_ed
            self.libro_editorial['values'] = list(self.editoriales_map.keys())
        except mariadb.Error as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar las editoriales: {e}")
        finally:
            conn.close()

    def load_autores(self):
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        self.autores_map.clear()
        self.autores_listbox.delete(0, tk.END)
        try:
            cursor.execute("SELECT ID_autor, A_nombre FROM autor ORDER BY A_nombre")
            autores = cursor.fetchall()
            for id_au, nombre_au in autores:
                self.autores_map[nombre_au] = id_au
                self.autores_listbox.insert(tk.END, nombre_au)
        except mariadb.Error as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar los autores: {e}")
        finally:
            conn.close()

    def load_generos(self):
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        self.generos_map.clear()
        self.generos_listbox.delete(0, tk.END)
        try:
            cursor.execute("SELECT ID_genero, G_nombre FROM genero ORDER BY G_nombre")
            generos = cursor.fetchall()
            for id_gen, nombre_gen in generos:
                self.generos_map[nombre_gen] = id_gen
                self.generos_listbox.insert(tk.END, nombre_gen)
        except mariadb.Error as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar los géneros: {e}")
        finally:
            conn.close()

    def insert_libro(self):
        isbn = self.libro_isbn.get()
        nombre = self.libro_nombre.get()
        precio = self.libro_precio.get()
        cantidad = self.libro_cantidad.get()
        editorial_nombre = self.libro_editorial.get()

        if not all([isbn, nombre, precio, cantidad, editorial_nombre]):
            messagebox.showwarning("Campos Vacíos", "Todos los campos del libro son obligatorios.")
            return

        editorial_id = self.editoriales_map.get(editorial_nombre)
        
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()

        try:
            query = "INSERT INTO libro (L_ISBN, L_nombre, L_Precio, L_Cantidad, ID_editorial) VALUES (?, ?, ?, ?, ?)"
            cursor.execute(query, (isbn, nombre, float(precio), int(cantidad), editorial_id))
            conn.commit()
            messagebox.showinfo("Éxito", "Libro insertado correctamente. Ahora puedes asignarle autores y géneros.")
        except mariadb.Error as e:
            messagebox.showerror("Error en Inserción", f"No se pudo insertar el libro: {e}")
        except ValueError:
            messagebox.showerror("Error de Formato", "Precio y cantidad deben ser números válidos.")
        finally:
            conn.close()

    def assign_autores_generos(self):
        isbn = self.libro_isbn.get()
        if not isbn:
            messagebox.showwarning("ISBN Vacío", "Inserta un libro primero o escribe el ISBN del libro a modificar.")
            return

        selected_autores_indices = self.autores_listbox.curselection()
        selected_generos_indices = self.generos_listbox.curselection()

        if not selected_autores_indices and not selected_generos_indices:
            messagebox.showwarning("Sin Selección", "No has seleccionado ningún autor o género para asignar.")
            return

        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        
        try:
            for i in selected_autores_indices:
                nombre_autor = self.autores_listbox.get(i)
                id_autor = self.autores_map.get(nombre_autor)
                cursor.execute("INSERT IGNORE INTO rel_a_l (ID_autor, L_ISBN) VALUES (?, ?)", (id_autor, isbn))

            for i in selected_generos_indices:
                nombre_genero = self.generos_listbox.get(i)
                id_genero = self.generos_map.get(nombre_genero)
                cursor.execute("INSERT IGNORE INTO rel_l_g (ID_genero, L_ISBN) VALUES (?, ?)", (id_genero, isbn))

            conn.commit()
            messagebox.showinfo("Éxito", "Autores y géneros asignados correctamente.")
            self.libro_isbn.delete(0, tk.END)
            self.libro_nombre.delete(0, tk.END)
            self.libro_precio.delete(0, tk.END)
            self.libro_cantidad.delete(0, tk.END)
            self.libro_editorial.set('')
            self.autores_listbox.selection_clear(0, tk.END)
            self.generos_listbox.selection_clear(0, tk.END)
        except mariadb.Error as e:
            messagebox.showerror("Error en Asignación", f"No se pudo asignar la relación: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    app = App()
    app.mainloop()