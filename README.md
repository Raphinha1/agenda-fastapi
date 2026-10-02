# Agenda modular con FastAPI

Aplicación de agenda de contactos basada en la guía de cátedra. Incluye API REST, SQLite con SQLModel, autenticación OAuth2 y JWT, vistas Jinja2, CORS y un middleware de tiempo de respuesta. Cada usuario ve y modifica solo sus propios contactos.

## Requisitos

- Python 3.12 o superior.
- Una terminal en el directorio `mi_agenda_fastapi`.

## Instalación y arranque

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
uvicorn main:app --reload
```

La base SQLite se crea automáticamente como `agenda.db`. Para conservar las sesiones entre reinicios, guarda una clave aleatoria estable en la variable `SECRET_KEY`. El archivo `.env.example` muestra las variables disponibles; la aplicación lee variables de entorno, no carga ese archivo automáticamente. `DATABASE_URL` también puede apuntar a PostgreSQL si instalas su controlador por separado.

Abre <http://127.0.0.1:8000/docs> para la API o <http://127.0.0.1:8000/views/agenda> para la interfaz web.

## Reto 1: comprobar OAuth2 en Swagger

1. En `/docs`, ejecuta `POST /auth/register` con un usuario nuevo, correo y contraseña de al menos 8 caracteres.
2. Pulsa **Authorize** e ingresa el nombre de usuario y la contraseña recién creados. Swagger llamará a `POST /auth/token`.
3. Ejecuta `POST /agenda` para crear un contacto. Prueba también `PUT /agenda/{contact_id}` y `DELETE /agenda/{contact_id}`. Las tres operaciones requieren el token; sin él responden `401`.
4. `GET /agenda` y `GET /agenda/{contact_id}` también requieren sesión, pues los contactos son privados.

Ejemplo de contacto:

```json
{"nombre":"María López","telefono":"8123456789","mail":"maria@example.com"}
```

## Reto 2: relación entre usuario y contacto

`Contacto.user_id` es una clave foránea a `Usuario.id`. El servidor asigna el dueño desde el JWT al crear un contacto. Las consultas y modificaciones filtran por `user_id`; un usuario diferente recibe `404` al intentar acceder a un contacto ajeno. El cliente no puede elegir ni cambiar el dueño.

## Reto 3: formulario HTML

La ruta `/views/login` permite iniciar sesión en el navegador con un usuario registrado. `/views/agenda` se renderiza con Jinja2, muestra solo sus contactos y tiene un formulario para agregarlos. La sesión web usa una cookie HTTP only y el formulario lleva un token de protección CSRF. **Salir** cierra la sesión web. Los clientes API siguen usando el token Bearer de OAuth2.

## Estructura

```text
main.py                 Entrada y configuración de FastAPI
src/config.py           Variables de entorno
src/database.py         Engine y sesiones SQLModel
src/models/             Usuario y Contacto
src/auth/               Contraseñas, JWT y dependencias
src/routers/            API de autenticación, agenda y vistas
src/middlewares/        Tiempo de respuesta
src/templates/          HTML Jinja2
static/                 Estilos CSS
tests/                  Pruebas de rutas y aislamiento
```

## Pruebas

```bash
pip install pytest httpx
python -m pytest -q
```

La configuración de `ALLOWED_ORIGINS` es una lista de orígenes separados por comas. El valor predeterminado permite los orígenes locales en el puerto 8000. Para publicar la aplicación, configura una clave estable y secreta, una base de datos administrada y los orígenes reales; `create_all` sirve para esta práctica y no reemplaza migraciones de esquema.
