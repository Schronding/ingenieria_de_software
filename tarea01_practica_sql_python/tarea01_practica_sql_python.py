import sqlite3

try:
    conn_lib = sqlite3.connect('libreria')
    cursor = conn_lib.cursor()

    print("¡Conexión a la base de datos 'libreria.db' establecida con éxito! 🎉")

    # --- Aquí es donde ejecutarías tus consultas SQL ---
    cursor.execute("SELECT * FROM libro;")
    cursor.execute("SELECT * FROM autor WHERE A_nombre LIKE '%Stephen King'")
    resultados = cursor.fetchall()
    print(resultados)

except sqlite3.Error as error:
    print("Error al conectar con la base de datos:", error)

finally:
    if 'connection' in locals() and conn_lib:
        conn_lib.close()
        print("La conexión SQLite ha sido cerrada.")