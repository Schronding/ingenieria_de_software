import sys
import time
import json
import os
import serial
import serial.tools.list_ports
import threading
import pymysql
from datetime import datetime, timedelta
import customtkinter as ctk
from tkinter import ttk, messagebox
import matplotlib
matplotlib.use("TkAgg") 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

# ============================================================
# CONFIGURACIÓN GLOBAL
# ============================================================
BAUD_RATE = 115200
ARCHIVO_APODOS = "device_nicknames.json"

# Memoria de Sesión
session_data = {
    "time": [],
    "temp": [],
    "hum": [],
    "pres": []
}

# Variables de estado
val_id_locked = None 
val_live_id = "---"
val_temp = 0.0
val_hum = 0.0
val_pres = 0.0
paquetes_recibidos = 0 

# Control
arduino = None
conexion_db = None
cursor_db = None
db_activa = False
ejecutando = True

# Datos DB
DB_HOST = "127.0.0.1"
DB_USER = "root"
DB_PASS = "1324" 
DB_NAME = "sensores"

# Estilo
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ============================================================
# GESTIÓN DE APODOS
# ============================================================
def cargar_apodos():
    if not os.path.exists(ARCHIVO_APODOS): return {}
    try:
        with open(ARCHIVO_APODOS, 'r') as f: return json.load(f)
    except: return {}

def guardar_apodo(id_real, nuevo_apodo):
    diccionario = cargar_apodos()
    diccionario[id_real] = nuevo_apodo
    try:
        with open(ARCHIVO_APODOS, 'w') as f: json.dump(diccionario, f); return True
    except: return False

apodos_cache = cargar_apodos()

# ============================================================
# HILO RECEPTOR
# ============================================================
def hilo_receptor():
    global val_id_locked, val_live_id, val_temp, val_hum, val_pres, paquetes_recibidos
    
    while ejecutando:
        if arduino and arduino.is_open:
            try:
                if arduino.in_waiting > 0:
                    linea = arduino.readline().decode('utf-8').strip()
                    if not linea or "INICIO" in linea: continue
                    
                    partes = linea.split(",")
                    if len(partes) >= 4:
                        try:
                            raw_id = partes[0]
                            t, h, p = float(partes[1]), float(partes[2]), float(partes[3])
                        except ValueError: continue 
                        
                        ahora = datetime.now()
                        
                        if val_id_locked is None:
                            val_id_locked = raw_id
                        
                        val_live_id = raw_id
                        val_temp, val_hum, val_pres = t, h, p
                        paquetes_recibidos += 1

                        session_data["time"].append(ahora)
                        session_data["temp"].append(t)
                        session_data["hum"].append(h)
                        session_data["pres"].append(p)
                        
                        # Intento simple de escritura (sin bloquear el hilo si falla)
                        if db_activa and cursor_db:
                            try:
                                sql = "INSERT INTO mediciones (temperatura, humedad, presion, fecha_hora) VALUES (%s, %s, %s, %s)"
                                cursor_db.execute(sql, (t, h, p, ahora))
                                conexion_db.commit()
                            except: pass
            except: time.sleep(0.1)
        else:
            time.sleep(0.1)

# ============================================================
# INTERFAZ GRÁFICA V10.0 (BUG FIXES)
# ============================================================
class ProfessionalLogger(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.use_fahrenheit = False 
        self.refresh_rate = 500
        self.graph_window_minutes = 1

        self.title("ESP32 Data Station V10 - Final Stable")
        self.geometry("1400x950")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.is_connected = False
        self.annot_dict = {} # Diccionario para guardar 1 tooltip por gráfica
        
        # Variables visuales
        self.var_db_status = ctk.StringVar(value="OFF")
        self.var_db_color = ctk.StringVar(value="#C62828")
        self.var_id_display = ctk.StringVar(value="---")
        self.var_alias_display = ctk.StringVar(value="---")

        self.cfg_show_grid = ctk.BooleanVar(value=True)
        self.cfg_show_tooltip = ctk.BooleanVar(value=True)
        self.cfg_layout_mode = ctk.StringVar(value="Separado (3 Filas)")
        
        self.init_sidebar()
        self.init_main_area()
        self.init_footer()
        
        self.escanear_puertos()
        self.reconectar_db() 
        self.update_ui_loop() 
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def init_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        ctk.CTkLabel(self.sidebar, text="DATA STATION", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, padx=20, pady=(25, 10))
        
        info_frame = ctk.CTkFrame(self.sidebar, fg_color="#263238")
        info_frame.grid(row=1, column=0, padx=15, pady=10, sticky="ew")
        
        ctk.CTkLabel(info_frame, text="ID SISTEMA (ESTABLE):", font=("Arial", 10, "bold"), text_color="gray").pack(pady=(5,0))
        ctk.CTkLabel(info_frame, textvariable=self.var_id_display, font=("Consolas", 14, "bold"), text_color="#4FC3F7").pack()
        
        ctk.CTkLabel(info_frame, text="ALIAS / APODO:", font=("Arial", 10, "bold"), text_color="gray").pack(pady=(5,0))
        ctk.CTkLabel(info_frame, textvariable=self.var_alias_display, font=("Arial", 16, "bold"), text_color="#FFB74D").pack(pady=(0,10))

        ctk.CTkLabel(self.sidebar, text="CONEXIÓN SERIAL", anchor="w", font=ctk.CTkFont(size=12, weight="bold")).grid(row=2, column=0, padx=20, pady=(20, 0), sticky="ew")
        self.combo_ports = ctk.CTkComboBox(self.sidebar, values=["Buscando..."])
        self.combo_ports.grid(row=3, column=0, padx=20, pady=5)
        
        btn_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_row.grid(row=4, column=0, padx=20, pady=5)
        self.btn_refresh = ctk.CTkButton(btn_row, text="↻", width=40, fg_color="gray30", command=self.escanear_puertos)
        self.btn_refresh.pack(side="left", padx=(0,5))
        self.btn_connect = ctk.CTkButton(btn_row, text="Conectar", width=140, fg_color="#2E7D32", hover_color="#1B5E20", command=self.toggle_connection)
        self.btn_connect.pack(side="left")

        ctk.CTkLabel(self.sidebar, text="BASE DE DATOS", anchor="w", font=ctk.CTkFont(size=12, weight="bold")).grid(row=6, column=0, padx=20, pady=(30, 0), sticky="ew")
        self.entry_db_name = ctk.CTkEntry(self.sidebar, placeholder_text="DB Name"); self.entry_db_name.insert(0, DB_NAME)
        self.entry_db_name.grid(row=7, column=0, padx=20, pady=5)
        self.entry_db_pass = ctk.CTkEntry(self.sidebar, placeholder_text="Password", show="*"); self.entry_db_pass.insert(0, DB_PASS)
        self.entry_db_pass.grid(row=8, column=0, padx=20, pady=5)

        status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        status_frame.grid(row=9, column=0, padx=20, pady=5)
        self.lbl_db_status = ctk.CTkLabel(status_frame, textvariable=self.var_db_status, text_color=self.var_db_color.get(), font=("Arial", 12, "bold"))
        self.lbl_db_status.pack(side="left", padx=5)
        ctk.CTkButton(status_frame, text="Reconectar", width=80, height=20, fg_color="#00695C", command=self.reconectar_db).pack(side="right")

    def init_main_area(self):
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")
        self.tab_dash = self.tabview.add("Monitor en Vivo")
        self.tab_history = self.tabview.add("Historial & Reportes")
        self.tab_settings = self.tabview.add("Ajustes")
        self.setup_dashboard_tab()
        self.setup_history_tab()
        self.setup_settings_tab()

    def init_footer(self):
        self.log_frame = ctk.CTkFrame(self, height=30, corner_radius=0, fg_color="#1a1a1a")
        self.log_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.lbl_flow = ctk.CTkLabel(self.log_frame, text="Sistema Listo.", font=("Consolas", 11), text_color="gray")
        self.lbl_flow.pack(side="left", padx=20)

    # --- DASHBOARD ---
    def setup_dashboard_tab(self):
        self.tab_dash.grid_columnconfigure((0,1,2), weight=1)
        self.tab_dash.grid_rowconfigure(2, weight=1)
        
        self.card_temp = self.crear_kpi(self.tab_dash, "TEMPERATURA", "--.--", "°C", 0, "#D32F2F")
        self.card_hum = self.crear_kpi(self.tab_dash, "HUMEDAD", "--.--", "%", 1, "#1976D2")
        self.card_pres = self.crear_kpi(self.tab_dash, "PRESIÓN", "----", "hPa", 2, "#388E3C")

        toolbar = ctk.CTkFrame(self.tab_dash, fg_color="transparent")
        toolbar.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(20, 0))
        self.btn_unit = ctk.CTkButton(toolbar, text="°C / °F", width=60, fg_color="#455A64", command=self.toggle_units)
        self.btn_unit.pack(side="left", padx=10)

        ctk.CTkLabel(toolbar, text="Visualizar:", font=("Arial", 12, "bold")).pack(side="left", padx=(20, 5))
        self.seg_time = ctk.CTkSegmentedButton(toolbar, values=["1 Min", "5 Min", "15 Min", "Todo"], command=self.set_time_window)
        self.seg_time.set("1 Min")
        self.seg_time.pack(side="left")

        self.graph_frame = ctk.CTkFrame(self.tab_dash, fg_color="transparent")
        self.graph_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=10)
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(6, 8))
        self.fig.patch.set_facecolor('#2b2b2b')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self.on_hover)
        self.redraw_graphs()

    def set_time_window(self, value):
        if value == "1 Min": self.graph_window_minutes = 1
        elif value == "5 Min": self.graph_window_minutes = 5
        elif value == "15 Min": self.graph_window_minutes = 15
        elif value == "Todo": self.graph_window_minutes = 0

    def toggle_units(self):
        self.use_fahrenheit = not self.use_fahrenheit
        self.btn_unit.configure(text="Modo: °F" if self.use_fahrenheit else "Modo: °C")

    # --- HISTORIAL ---
    def setup_history_tab(self):
        self.tab_history.grid_columnconfigure(0, weight=1)
        self.tab_history.grid_rowconfigure(2, weight=1)

        quick_frame = ctk.CTkFrame(self.tab_history)
        quick_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkLabel(quick_frame, text="Selección Rápida:", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        ctk.CTkButton(quick_frame, text="Última Hora", width=100, fg_color="#5C6BC0", command=lambda: self.set_range("hora")).pack(side="left", padx=5)
        ctk.CTkButton(quick_frame, text="Hoy", width=80, fg_color="#5C6BC0", command=lambda: self.set_range("hoy")).pack(side="left", padx=5)
        ctk.CTkButton(quick_frame, text="Ayer", width=80, fg_color="#5C6BC0", command=lambda: self.set_range("ayer")).pack(side="left", padx=5)

        manual_frame = ctk.CTkFrame(self.tab_history, fg_color="transparent")
        manual_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.entry_start = ctk.CTkEntry(manual_frame, width=160, placeholder_text="Inicio")
        self.entry_start.pack(side="left", padx=5)
        ctk.CTkLabel(manual_frame, text=" ➜ ").pack(side="left")
        self.entry_end = ctk.CTkEntry(manual_frame, width=160, placeholder_text="Fin")
        self.entry_end.pack(side="left", padx=5)
        ctk.CTkButton(manual_frame, text="BUSCAR EN BD", fg_color="#FBC02D", text_color="black", hover_color="#F9A825", command=self.consultar_db_seguro).pack(side="left", padx=20)

        self.tree_hist = ttk.Treeview(self.tab_history, columns=("fecha", "temp", "hum", "pres"), show="headings")
        self.tree_hist.heading("fecha", text="Fecha Hora"); self.tree_hist.column("fecha", width=180)
        self.tree_hist.heading("temp", text="Temp"); self.tree_hist.column("temp", width=80)
        self.tree_hist.heading("hum", text="Hum"); self.tree_hist.column("hum", width=80)
        self.tree_hist.heading("pres", text="Pres"); self.tree_hist.column("pres", width=80)
        self.tree_hist.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

    def set_range(self, mode):
        now = datetime.now()
        start, end = "", ""
        if mode == "hora":
            start = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
            end = now.strftime("%Y-%m-%d %H:%M:%S")
        elif mode == "hoy":
            start = now.strftime("%Y-%m-%d 00:00:00")
            end = now.strftime("%Y-%m-%d 23:59:59")
        elif mode == "ayer":
            yesterday = now - timedelta(days=1)
            start = yesterday.strftime("%Y-%m-%d 00:00:00")
            end = yesterday.strftime("%Y-%m-%d 23:59:59")
        self.entry_start.delete(0, 'end'); self.entry_start.insert(0, start)
        self.entry_end.delete(0, 'end'); self.entry_end.insert(0, end)

    # --- FUNCIÓN DB BLINDADA CONTRA 'CLOSED FILE' ---
    def consultar_db_seguro(self):
        global conexion_db, cursor_db, db_activa
        
        s, e = self.entry_start.get(), self.entry_end.get()
        if not s or not e: messagebox.showwarning("!", "Faltan fechas"); return

        for item in self.tree_hist.get_children(): self.tree_hist.delete(item)

        # Función interna para intentar la consulta
        def ejecutar_query():
            sql = "SELECT fecha_hora, temperatura, humedad, presion FROM mediciones WHERE fecha_hora BETWEEN %s AND %s ORDER BY fecha_hora DESC"
            cursor_db.execute(sql, (s, e))
            return cursor_db.fetchall()

        try:
            # Intento 1: Directo
            rows = ejecutar_query()
        except Exception:
            # Si falla (ej. read of closed file), forzamos reinicio total de conexión
            print("Conexión perdida. Reiniciando conexión DB...")
            try:
                if conexion_db: conexion_db.close()
            except: pass
            
            # Recreamos TODO
            try:
                conexion_db = pymysql.connect(host=DB_HOST, user=DB_USER, password=self.entry_db_pass.get(), database=self.entry_db_name.get())
                cursor_db = conexion_db.cursor()
                db_activa = True
                self.var_db_status.set("ON"); self.var_db_color.set("#00E676"); self.lbl_db_status.configure(text_color="#00E676")
                
                # Intento 2: Con conexión fresca
                rows = ejecutar_query()
            except Exception as ex_final:
                messagebox.showerror("Error Fatal DB", f"No se pudo reconectar.\n{ex_final}")
                return

        if not rows: 
            messagebox.showinfo("Info", "Sin datos en este rango.")
            return
        
        for r in rows:
            t_val = r[1]
            if self.use_fahrenheit: t_val = (t_val * 9/5) + 32
            self.tree_hist.insert("", "end", values=(r[0], f"{t_val:.2f}", r[2], r[3]))

    # --- AJUSTES ---
    def setup_settings_tab(self):
        self.tab_settings.grid_columnconfigure(0, weight=1)
        frame = ctk.CTkFrame(self.tab_settings); frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Configuración Visual", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="Distribución de Gráficas:").pack(anchor="w", padx=20)
        self.opt_layout = ctk.CTkOptionMenu(frame, values=["Separado (3 Filas)", "Compacto (2 Filas)", "Unificado (1 Fila)"], variable=self.cfg_layout_mode, command=self.redraw_graphs)
        self.opt_layout.pack(anchor="w", padx=20, pady=5)

        ctk.CTkSwitch(frame, text="Mostrar Grid (Cuadrícula)", variable=self.cfg_show_grid, command=self.redraw_graphs).pack(anchor="w", padx=20, pady=10)
        ctk.CTkSwitch(frame, text="Mostrar Tooltips", variable=self.cfg_show_tooltip).pack(anchor="w", padx=20, pady=5)

        ctk.CTkLabel(frame, text="Velocidad de Gráfica (ms):").pack(anchor="w", padx=20, pady=(15,0))
        self.slider = ctk.CTkSlider(frame, from_=100, to=2000, number_of_steps=20, command=self.update_rate)
        self.slider.set(self.refresh_rate)
        self.slider.pack(anchor="w", padx=20, pady=5)
        self.lbl_rate = ctk.CTkLabel(frame, text=f"{self.refresh_rate} ms")
        self.lbl_rate.pack(anchor="w", padx=20)

        frame_dev = ctk.CTkFrame(self.tab_settings); frame_dev.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(frame_dev, text="Renombrar Dispositivo Actual", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=10)
        self.entry_nick = ctk.CTkEntry(frame_dev, placeholder_text="Nuevo Alias")
        self.entry_nick.pack(side="left", padx=20, pady=10)
        ctk.CTkButton(frame_dev, text="Guardar Alias", command=self.guardar_alias).pack(side="left")

    def update_rate(self, val):
        self.refresh_rate = int(val)
        self.lbl_rate.configure(text=f"{int(val)} ms")

    def guardar_alias(self):
        if val_id_locked is None:
            messagebox.showwarning("!", "No hay un ID de sistema detectado.")
            return
        new_nick = self.entry_nick.get()
        if new_nick:
            guardar_apodo(val_id_locked, new_nick)
            apodos_cache[val_id_locked] = new_nick
            self.var_alias_display.set(new_nick)
            self.entry_nick.delete(0, 'end')
            messagebox.showinfo("OK", "Apodo guardado.")

    def redraw_graphs(self, _=None):
        self.fig.clear()
        mode, grid = self.cfg_layout_mode.get(), self.cfg_show_grid.get()
        self.lines_dict, self.axes_dict = {}, {}
        self.annot_dict = {} # Limpiamos referencias de tooltips

        if mode == "Separado (3 Filas)":
            ax1 = self.fig.add_subplot(311)
            ax2 = self.fig.add_subplot(312, sharex=ax1)
            ax3 = self.fig.add_subplot(313, sharex=ax1)
            self.lines_dict['t'] = self.setup_axis(ax1, "Temperatura", "#D32F2F", grid)
            self.lines_dict['h'] = self.setup_axis(ax2, "Humedad", "#1976D2", grid)
            self.lines_dict['p'] = self.setup_axis(ax3, "Presión", "#388E3C", grid)
            self.axes_dict = {'t': ax1, 'h': ax2, 'p': ax3}
            plt.subplots_adjust(hspace=0.5, top=0.95, bottom=0.15)
        elif mode == "Compacto (2 Filas)":
            ax1 = self.fig.add_subplot(211); ax2 = ax1.twinx(); ax3 = self.fig.add_subplot(212, sharex=ax1)
            self.lines_dict['t'] = self.setup_axis(ax1, "Temperatura", "#D32F2F", grid)
            self.lines_dict['h'] = self.setup_axis(ax2, "Humedad", "#1976D2", False)
            self.lines_dict['p'] = self.setup_axis(ax3, "Presión", "#388E3C", grid)
            ax2.spines['right'].set_color('#1976D2'); ax2.tick_params(axis='y', colors='#1976D2')
            self.axes_dict = {'t': ax1, 'h': ax2, 'p': ax3}
            plt.subplots_adjust(hspace=0.3, top=0.95, bottom=0.15)
        elif mode == "Unificado (1 Fila)":
            ax1 = self.fig.add_subplot(111); ax2 = ax1.twinx(); ax3 = ax1.twinx()
            ax3.spines["right"].set_position(("axes", 1.15))
            self.lines_dict['t'] = self.setup_axis(ax1, "Temperatura", "#D32F2F", grid)
            self.lines_dict['h'] = self.setup_axis(ax2, "Humedad", "#1976D2", False)
            self.lines_dict['p'] = self.setup_axis(ax3, "Presión", "#388E3C", False)
            ax2.spines['right'].set_color('#1976D2'); ax2.tick_params(axis='y', colors='#1976D2')
            ax3.spines['right'].set_color('#388E3C'); ax3.tick_params(axis='y', colors='#388E3C')
            self.axes_dict = {'t': ax1, 'h': ax2, 'p': ax3}
            plt.subplots_adjust(right=0.8, top=0.95, bottom=0.15)
        
        for ax in self.fig.axes:
            ax.xaxis_date()
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

        # CREAMOS 1 ANOTACIÓN POR CADA EJE PARA EVITAR CLIPPING
        for key, ax in self.axes_dict.items():
            annot = ax.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points", 
                                bbox=dict(boxstyle="round", fc="#1a1a1a", ec="white"), color="white")
            annot.set_visible(False)
            self.annot_dict[ax] = annot # Guardamos referencia asociada al eje

        self.canvas.draw()

    def setup_axis(self, ax, label, color, grid):
        ax.set_facecolor('#202020'); ax.tick_params(colors='gray', labelsize=8)
        for spine in ax.spines.values(): spine.set_edgecolor('#404040')
        if grid: ax.grid(True, color='#404040', linestyle='--', linewidth=0.5)
        ax.set_ylabel(label, color=color, fontweight='bold')
        l, = ax.plot([], [], color=color, linewidth=1.5)
        return l

    def update_ui_loop(self):
        if self.is_connected:
            current_alias = apodos_cache.get(val_id_locked, "Sin Apodo")
            self.var_id_display.set(val_id_locked if val_id_locked else "Esperando...")
            self.var_alias_display.set(current_alias)
            self.lbl_flow.configure(text=f"Live ID: {val_live_id} | Paquetes: {paquetes_recibidos}")
        else:
            self.lbl_flow.configure(text="Desconectado.")

        t_show = (val_temp * 9/5) + 32 if self.use_fahrenheit else val_temp
        unit = "°F" if self.use_fahrenheit else "°C"
        self.card_temp.configure(text=f"{t_show:.2f}"); self.card_temp.master.winfo_children()[2].configure(text=unit)
        self.card_hum.configure(text=f"{val_hum:.2f}")
        self.card_pres.configure(text=f"{val_pres:.0f}")

        if len(session_data["time"]) > 0:
            if self.graph_window_minutes > 0:
                cutoff_time = session_data["time"][-1] - timedelta(minutes=self.graph_window_minutes)
                indices = [i for i, t in enumerate(session_data["time"]) if t > cutoff_time]
                start_idx = indices[0] if indices else 0
            else:
                start_idx = 0

            times = session_data["time"][start_idx:]
            raw_temps = session_data["temp"][start_idx:]
            hums = session_data["hum"][start_idx:]
            press = session_data["pres"][start_idx:]
            plot_temps = [(x * 9/5 + 32) if self.use_fahrenheit else x for x in raw_temps]

            if 't' in self.lines_dict: 
                self.lines_dict['t'].set_data(times, plot_temps)
                self.autoscale(self.lines_dict['t'].axes, times, plot_temps)
            if 'h' in self.lines_dict: 
                self.lines_dict['h'].set_data(times, hums)
                self.autoscale(self.lines_dict['h'].axes, times, hums)
            if 'p' in self.lines_dict: 
                self.lines_dict['p'].set_data(times, press)
                self.autoscale(self.lines_dict['p'].axes, times, press)
            self.canvas.draw_idle()

        self.after(self.refresh_rate, self.update_ui_loop)

    def autoscale(self, ax, x, y):
        if not x or not y: return
        ax.set_xlim(x[0], x[-1])
        mi, ma = min(y), max(y)
        m = (ma - mi) * 0.1 if ma != mi else 1.0
        ax.set_ylim(mi - m, ma + m)

    # --- TOOLTIP MULTI-EJE CORREGIDO ---
    def on_hover(self, event):
        # 1. Ocultar todos los tooltips primero
        for annot in self.annot_dict.values():
            annot.set_visible(False)

        if not self.cfg_show_tooltip.get() or not event.inaxes: 
            self.canvas.draw_idle()
            return

        # 2. Obtener el tooltip que corresponde a la gráfica donde está el mouse
        annot = self.annot_dict.get(event.inaxes)
        if not annot: return

        try:
            x_date = mdates.num2date(event.xdata).replace(tzinfo=None)
            times = session_data["time"] 
            if not times: return
            idx = min(range(len(times)), key=lambda i: abs((times[i] - x_date).total_seconds()))
            
            raw_t = session_data["temp"][idx]
            disp_t = (raw_t * 9/5) + 32 if self.use_fahrenheit else raw_t
            unit = "°F" if self.use_fahrenheit else "°C"
            
            # Ahora annot pertenece al eje correcto, así que se verá siempre
            annot.xy = (mdates.date2num(times[idx]), event.ydata) # Seguimos altura del mouse
            annot.set_text(f"{times[idx].strftime('%H:%M:%S')}\nT: {disp_t:.1f}{unit}\nH: {session_data['hum'][idx]}%\nP: {session_data['pres'][idx]}")
            annot.set_visible(True)
            self.canvas.draw_idle()
        except: pass

    def crear_kpi(self, p, t, v, u, c, color):
        f = ctk.CTkFrame(p, border_color=color, border_width=2); f.grid(row=0, column=c, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(f, text=t, font=("Arial", 11, "bold"), text_color="gray").pack(pady=(5,0))
        l = ctk.CTkLabel(f, text=v, font=("Arial", 28, "bold")); l.pack()
        ctk.CTkLabel(f, text=u, font=("Arial", 12)).pack(pady=(0,5)); return l

    def escanear_puertos(self):
        puertos = [p.device for p in serial.tools.list_ports.comports()]
        self.combo_ports.configure(values=puertos if puertos else ["Sin Puertos"])
        if puertos: self.combo_ports.set(puertos[0])

    def toggle_connection(self):
        global arduino, val_id_locked
        puerto = self.combo_ports.get()
        if not self.is_connected:
            try:
                arduino = serial.Serial(puerto, BAUD_RATE, timeout=2)
                self.is_connected = True
                val_id_locked = None 
                self.btn_connect.configure(text="Desconectar", fg_color="#C62828")
                self.combo_ports.configure(state="disabled")
            except Exception as e: messagebox.showerror("Error", f"{e}")
        else:
            self.is_connected = False
            if arduino: arduino.close()
            self.btn_connect.configure(text="Conectar", fg_color="#2E7D32")
            self.combo_ports.configure(state="normal")
            
    def reconectar_db(self):
        global conexion_db, cursor_db, db_activa
        try:
            if conexion_db: conexion_db.close()
            conexion_db = pymysql.connect(host=DB_HOST, user=DB_USER, password=self.entry_db_pass.get(), database=self.entry_db_name.get())
            cursor_db = conexion_db.cursor()
            db_activa = True
            self.var_db_status.set("ON"); self.var_db_color.set("#00E676"); self.lbl_db_status.configure(text_color="#00E676")
        except: 
            db_activa = False
            self.var_db_status.set("OFF"); self.var_db_color.set("#C62828"); self.lbl_db_status.configure(text_color="#C62828")

    def on_closing(self):
        global ejecutando; ejecutando = False; self.destroy(); sys.exit()

if __name__ == "__main__":
    t = threading.Thread(target=hilo_receptor, daemon=True); t.start()
    app = ProfessionalLogger(); app.mainloop()