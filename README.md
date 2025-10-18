# Flask Middleware

Sistema de middleware JWT para Flask con soporte para múltiples clientes, revocación selectiva de tokens y auditoría completa. Diseñado para ser flexible, escalable y fácil de mantener sin necesidad de base de datos.

## Características Principales

- **Autenticación JWT Flexible**: Acepta múltiples API_KEYs firmadas con JWT_SECRET_KEY
- **Revocación Selectiva**: Sistema de blacklist para revocar tokens individuales
- **Sin Base de Datos**: Usa archivos JSON para persistencia
- **Hot-Reload**: Detección automática de cambios en blacklist
- **CLI Integrado**: Herramienta completa para gestión de tokens y administración
- **Registro de Tokens**: Auditoría completa de tokens emitidos
- **Identificación de Clientes**: Logs detallados con información del cliente
- **Tests Completos**: Cobertura >90% con pytest

## Índice

* [Instalación y Configuración](#instalación-y-configuración)
* [Uso del CLI Integrado](#uso-del-cli-integrado)
* [Gestión de Tokens](#gestión-de-tokens)
* [API Endpoints](#api-endpoints)
* [Desarrollo y Testing](#desarrollo-y-testing)
* [Producción](#producción)
* [Documentación Adicional](#documentación-adicional)
* [Contribución](#contribución)

## Instalación y Configuración

### Requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Configuración Rápida

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd flask_middleware
```

2. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

3. **Levantar la aplicación**
```bash
# Desarrollo
docker-compose -f docker-compose-dev.yml up -d --build

# Producción
docker-compose -f docker-compose-prod.yml up -d --build
```

## Uso del CLI Integrado

El CLI está integrado en la aplicación principal. Puedes usarlo de dos formas:

### Desde el contenedor Docker

```bash
# Acceder al contenedor
docker exec -it flask-middleware-dev bash

# Ejecutar comandos
flask tokens generate --issued-to cliente --issuer api
flask tokens list
flask tokens stats
```

### Desde el código fuente

```bash
cd backend
flask tokens generate --issued-to cliente --issuer api
flask tokens list
flask tokens stats
```

## Gestión de Tokens

### Comandos Disponibles

```bash
# Generar nuevo token
flask tokens generate --issued-to "cliente-api" --issuer "mi-servicio"

# Listar tokens
flask tokens list
flask tokens list --active-only

# Consultar token específico
flask tokens query --jti "<JTI_DEL_TOKEN>"

# Revocar token
flask tokens revoke --jti "<JTI>" --reason "Token comprometido"

# Restaurar token
flask tokens unrevoke --jti "<JTI>"

# Ver estadísticas
flask tokens stats
```

### Ejemplos de Uso

```bash
# Generar token para cliente de producción
flask tokens generate \
  --issued-to "cliente-prod" \
  --issuer "api-produccion" \
  --notes "Cliente corporativo - Contrato #123"

# Ver todos los tokens activos
flask tokens list --active-only

# Revocar token comprometido
flask tokens revoke \
  --jti "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  --reason "Token comprometido"
```

## API Endpoints

### Autenticación

- `GET /api/v1/` - Endpoint protegido (requiere JWT)
- `GET /api/health` - Health check

### Documentación

- Desarrollo: `http://localhost:5000/docs`
- Ver documentación completa en [backend/docs/](backend/docs/)

## Desarrollo y Testing

### Ejecutar Tests

```bash
# Tests básicos
docker exec -it flask-middleware-dev pytest

# Tests con cobertura
docker exec -it flask-middleware-dev pytest --cov=core.middleware --cov-report=term-missing

# Verificar cobertura mínima (90%)
docker exec -it flask-middleware-dev pytest --cov=core.middleware --cov-fail-under=90
```

### Estructura del Proyecto

```
backend/
├── app.py               # Factory de aplicación Flask
├── core/                # Lógica de negocio
│   ├── config.py        # Configuración por ambiente
│   ├── middleware.py     # Middleware JWT
│   ├── token_blacklist.py
│   └── token_registry.py
├── scripts/             # Herramientas CLI
│   └── token_cli.py     # CLI de tokens (integrado)
├── routers/             # Rutas de la API
├── schemas/             # Esquemas de validación
├── logs/                # Configuración de logging
├── data/                # Persistencia (JSON)
└── tests/               # Tests unitarios
```

## Producción

### Configuración de Producción

```bash
# Usar docker-compose-prod.yml
docker-compose -f docker-compose-prod.yml up -d --build
```

### Variables de Entorno Requeridas

```bash
ENVIRONMENT=production
JWT_SECRET_KEY=your-secure-jwt-secret
TOKEN_API_KEY=your-secure-api-key
SENTRY_DSN=your-sentry-dsn
```

### Monitoreo

- Logs: `/backend/logs/`
- Health check: `GET /api/health`
- Métricas: Integración con Sentry (producción)

## Documentación Adicional

- [Guía de Inicio Rápido](backend/docs/QUICKSTART.md) - Configuración y primeros pasos
- [Documentación de Autenticación](backend/docs/authentication.md) - Sistema JWT completo
- [CLI de Tokens](backend/scripts/README.md) - Gestión de tokens

## Contribución

1. Fork el repositorio
2. Crear feature branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit los cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request