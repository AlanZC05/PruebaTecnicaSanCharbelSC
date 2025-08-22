# PruebaTecnicaSanCharbelSC
Requerimientos
Python 3.8 o superior
MySQL (o la base de datos que hayas usado)
Navegador web
Conexión a internet (para consumir la API)

También necesitarás instalar algunas librerías de Python:
Flask
Flask-Bcrypt
Requests
python-dotenv
wikipedia-api
unidecode

Pasos para ejecutar el proyecto
Clonar el repositorio
Copia el proyecto desde GitHub a tu computadora usando el enlace del repositorio público.

Instalar dependencias
Abre una terminal y asegúrate de instalar todas las librerías necesarias de Python. Esto permite que el proyecto funcione correctamente.

Crea una base de datos en MySQL con el nombre de BloomHub

Ejecuta el script incluido en el repositorio para crear las tablas necesarias (usuarios, información de la API, etc.).

CREATE DATABASE BloomHub;

CREATE TABLE usuarios (
    id INT PRIMARY KEY,
    nombre VARCHAR(255),
    correo VARCHAR(255),
    contrasena VARCHAR(255),
    fecha_creacion DATE
);

Correr la aplicación

Inicia el proyecto desde la terminal.

Ingresa con un usuario de prueba (usuario: alan123@gmail.com, contraseña:123) o tambien se puede crear uno nuevo
