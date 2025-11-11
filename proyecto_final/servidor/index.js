// 1. Importar las bibliotecas necesarias
const express = require('express');
const cors = require('cors');
require('dotenv').config(); // NUEVO: Cargar variables de entorno

// NUEVO: Importar el 'Pool' de node-postgres
const { Pool } = require('pg');

// 2. Inicializar la aplicación de Express
const app = express();
const PORT = 5000;

// NUEVO: Configurar el Pool de Conexiones
// El Pool maneja eficientemente las conexiones a la base de datos
const pool = new Pool({
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    host: process.env.DB_HOST,
    port: process.env.DB_PORT,
    database: process.env.DB_DATABASE,
});

// 3. Configurar los "Middlewares"
app.use(cors());
app.use(express.json());

// 4. Definir el endpoint (MODIFICADO para ser async y usar la DB)
app.post('/api/datos', async (req, res) => { // async es clave
    
    // req.body contiene el JSON que envió el ESP-32
    const datosRecibidos = req.body;

    console.log('¡Datos recibidos desde el ESP-32!');
    console.log(datosRecibidos);

    // NUEVO: Lógica para insertar en PostgreSQL
    try {
        // Extraemos los datos (asegúrate que el ESP32 envíe estos nombres)
        // Recordatorio: Guardamos en unidades del SI
        const { temperatura_k, humedad_relativa, presion_pa } = datosRecibidos;

        // Definimos la consulta SQL
        const sqlQuery = `
            INSERT INTO mediciones (temperatura_k, humedad_relativa, presion_pa) 
            VALUES ($1, $2, $3)
            RETURNING id_medicion;
        `;
        
        // Ejecutamos la consulta
        // Usamos $1, $2, etc., para pasar los valores de forma segura (previene inyección SQL)
        const resultado = await pool.query(sqlQuery, [temperatura_k, humedad_relativa, presion_pa]);

        console.log(`Datos insertados con éxito. ID de la nueva medición: ${resultado.rows[0].id_medicion}`);
        console.log('-----------------------------------');

        // Respondemos al ESP-32 para que sepa que todo salió bien
        res.status(201).json({ 
            status: 'ok', 
            mensaje: 'Datos insertados correctamente' 
        });

    } catch (error) {
        // NUEVO: Manejo de errores de la base de datos
        console.error('Error al insertar en la base de datos:', error);
        console.log('-----------------------------------');
        res.status(500).json({
            status: 'error',
            mensaje: 'Error interno del servidor al guardar los datos'
        });
    }
});

// 5. Iniciar el servidor
app.listen(PORT, '0.0.0.0',() => {
    console.log(`Servidor iniciado en http://localhost:${PORT}`);
    console.log('Esperando datos del ESP-32 en el endpoint /api/datos...');
});