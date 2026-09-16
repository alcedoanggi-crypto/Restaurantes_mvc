# 🍅 La Sobremesa — Sistema de Gestión de Restaurante

Sistema de **pedidos y cocina** para restaurante, construido con **Flask + SQLAlchemy**
siguiendo una arquitectura **MVC** limpia. Incluye POS de meseros, pantalla de cocina
(KDS) en tiempo real, caja/facturación con cierre diario, gestión de menú, mesas,
inventario de insumos y un dashboard administrativo con gráficos (Chart.js).

## Arquitectura MVC

```
restaurante-mvc/
├── run.py                  # punto de entrada
├── config.py               # configuración (SQLite por defecto, PostgreSQL vía DATABASE_URL)
├── seed.py                 # datos de demostración
└── app/
    ├── __init__.py         # application factory + registro de blueprints
    ├── extensions.py       # db, login_manager, migrate
    ├── security.py         # roles y decorador @roles_required
    ├── models/             # MODELO  — SQLAlchemy (usuarios, mesas, categorías,
    │                       #           platillos, pedidos, detalle_pedidos,
    │                       #           empleados, facturas, insumos)
    ├── controllers/        # CONTROLADOR — blueprints (auth, dashboard, pos, cocina,
    │                       #               mesas, caja, menu, inventario, personal, api)
    ├── services/           # lógica de negocio / reportes
    ├── templates/          # VISTA — Jinja2 + Bootstrap 5
    └── static/             # CSS (paleta con variables), JS (Chart.js, KDS, POS)
```

## Roles

| Rol | Acceso |
|-----|--------|
| **administrador** | Todo |
| **mesero** | Toma de pedidos (POS), mesas, ver cocina |
| **cocina** | KDS, menú, inventario |
| **cajero** | Dashboard, caja/facturación, cierre, mesas |

## Puesta en marcha

```powershell
cd restaurante-mvc
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

copy .env.example .env        # opcional: ajustar SECRET_KEY / DATABASE_URL

python seed.py                # crea las tablas y carga datos demo
python run.py                 # http://127.0.0.1:5000
```

### Usuarios de demostración

| Usuario | Contraseña |
|---------|-----------|
| `admin` | `admin123` |
| `mesero` | `mesero123` |
| `cocina` | `cocina123` |
| `cajero` | `cajero123` |

## PostgreSQL

El proyecto ya viene configurado para PostgreSQL en el `.env`:

```
DATABASE_URL=postgresql://restaurante:123456@localhost:5432/restaurante
```

`config.py` fuerza el driver **psycopg v3** (`postgresql+psycopg://`), ya que
psycopg2 no compila en Python 3.13. Basta con instalarlo:

```powershell
pip install "psycopg[binary]"
```

Crear el rol y la base (una sola vez, como superusuario `postgres`):

```sql
CREATE ROLE restaurante LOGIN PASSWORD '123456';
CREATE DATABASE restaurante OWNER restaurante;
GRANT ALL PRIVILEGES ON DATABASE restaurante TO restaurante;
```

Luego `python seed.py --reset` crea las 9 tablas y carga los datos demo.
Para volver a SQLite, comenta la línea `DATABASE_URL` en `.env`.

## Migraciones (opcional)

El proyecto incluye Flask-Migrate:

```powershell
flask --app run db init
flask --app run db migrate -m "esquema inicial"
flask --app run db upgrade
```

## Paleta de diseño

Definida como variables CSS en `app/static/css/theme.css`:

| Token | Color |
|-------|-------|
| `--tomate` | `#DC2626` |
| `--naranja` | `#EA580C` |
| `--crema` | `#FEF3C7` |
| `--carbon` | `#1C1917` |

- **Login:** fondo de ingredientes desenfocado + tarjeta *glassmorphism*.
- **KDS:** tarjetas con semáforo verde → amarillo → rojo según minutos de espera
  (`KDS_WARN_MIN`, `KDS_LATE_MIN` en `config.py`).
- Tipografía *Playfair Display* (serif) en encabezados, *Inter* en el cuerpo.

## Tiempo real

La pantalla de cocina y el resumen de mesas se refrescan por **polling AJAX**
(`/api/cocina`, `/api/mesas`) cada 5–7 s. No requiere WebSockets.
