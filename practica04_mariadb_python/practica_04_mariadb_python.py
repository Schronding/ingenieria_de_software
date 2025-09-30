import mariadb
import sys
import os 
from dotenv import load_dotenv 

load_dotenv()

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASS")
db_host = os.getenv("DB_HOST")
db_port = int(os.getenv("DB_PORT")) 
db_name = os.getenv("DB_NAME")
db_path = os.getenv("DB_PATH")

try:
    conn = mariadb.connect(
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name
    )
    print(f"Conexión exitosa a la base de datos en: {db_path}")

except mariadb.Error as e:
    print(f"Error al conectar a MariaDB: {e}")
    sys.exit(1)

cursor = conn.cursor()

try:
    print("Todos los autores")
    cursor.execute("SELECT * FROM autor")
    for fila in cursor.fetchall():
        print(fila)

    print("\nBuscar a 'Stephen King'")
    query_sk = "SELECT * FROM autor WHERE A_nombre LIKE ?"
    cursor.execute(query_sk, ('%Stephen King%',))
    for fila in cursor.fetchall():
        print(fila)

    print("\nAutores finados, con Nobel, nacidos en marzo")
    query_nobel = """
        SELECT A_nombre, A_biografia, A_fecha_n FROM autor
        WHERE A_finado = 'TRUE'
        AND A_biografia LIKE ?
        AND A_fecha_n LIKE ?
    """
    cursor.execute(query_nobel, ('%Nobel%', '__/03/%'))
    for fila in cursor.fetchall():
        print(fila)

    print("\nModificando tabla y actualizando datos")
    
    try:
        cursor.execute("ALTER TABLE autor ADD nacionalidad VARCHAR(100) NOT NULL")
        print("Columna 'nacionalidad' agregada a la tabla 'autor' exitosamente.")
    except mariadb.Error as e:
        if "Duplicate column name" in str(e):
            print("La columna 'nacionalidad' ya existe. Omitiendo ALTER TABLE.")
        else:
            raise e

    nacionalidades = {
        1: 'colombiana', 2: 'chilena', 3: 'peruana', 4: 'argentina',
        5: 'mexicana', 6: 'mexicana', 7: 'chilena', 8: 'argentina',
        9: 'mexicana', 10: 'mexicana', 11: 'estadounidense', 12: 'estadounidense',
        13: 'británica', 14: 'británica', 15: 'inglesa', 16: 'británica'
    }

    query_update = "UPDATE autor SET nacionalidad = ? WHERE ID_autor = ?"
    for id_autor, nacionalidad in nacionalidades.items():
        cursor.execute(query_update, (nacionalidad, id_autor))
    
    conn.commit()
    print(f"{cursor.rowcount * len(nacionalidades)} registros de nacionalidad actualizados correctamente.")
    print("Cambios guardados permanentemente en la base de datos (commit).")

    print("\nVerificando actualización del autor con ID 1:")
    cursor.execute("SELECT ID_autor, A_nombre, nacionalidad FROM autor WHERE ID_autor = 1")
    print(cursor.fetchone())

except mariadb.Error as e:
    print(f"Error durante la ejecución de las consultas: {e}")

finally:
    conn.close()
    print("\nConexión a MariaDB cerrada.")