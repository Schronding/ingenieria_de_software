// 1. Importar las bibliotecas necesarias
const express = require('express'); // Framework para el servidor
const cors = require('cors');     // Middleware para permitir peticiones web

// 2. Inicializar la aplicación de Express
const app = express();
const PORT = 5000; // El puerto donde correrá el servidor

// 3. Configurar los "Middlewares"
app.use(cors()); // Permite peticiones de cualquier origen (tu futura web)
app.use(express.json()); // MUY IMPORTANTE: Parsea el JSON que enviará el ESP-32

// 4. Definir el endpoint (la URL) para recibir datos
// Escuchará peticiones POST en http://localhost:5000/api/datos
app.post('/api/datos', (req, res) => {
    
    // req.body contiene el JSON que envió el ESP-32
    const datosRecibidos = req.body;

    console.log('¡Datos recibidos desde el ESP-32!');
    console.log(datosRecibidos);
    console.log('-----------------------------------');

    // Respondemos al ESP-32 para que sepa que todo salió bien
    res.status(201).json({ 
        status: 'ok', 
        mensaje: 'Datos recibidos correctamente' 
    });
});

// 5. Iniciar el servidor
app.listen(PORT, () => {
    console.log(`Servidor iniciado en http://localhost:${PORT}`);
    console.log('Esperando datos del ESP-32 en el endpoint /api/datos...');
});