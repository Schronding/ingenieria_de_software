import sqlite3

try:
    conn_lib = sqlite3.connect('/home/schronding/repos/undergrad_in_technology/ingenieria_de_software/tarea01_practica_sql_python/libreria')
    cursor = conn_lib.cursor()

    print("¡Conexión a la base de datos 'libreria.db' establecida con éxito!")

    # --- Consultas SQL ---
    cursor.execute("SELECT * FROM genero")
    for ficha in cursor.fetchall():
        print(ficha)
    
except sqlite3.Error as error:
    print("Error al conectar con la base de datos:", error)

finally:
    if 'connection' in locals() and conn_lib:
        cursor.close()
        print("El cursor SQLite ha sido cerrado.")
        conn_lib.close()
        print("La conexión SQLite ha sido cerrada.")
