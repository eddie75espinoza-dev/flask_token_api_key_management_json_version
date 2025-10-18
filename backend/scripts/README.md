# Token Management CLI

Herramienta de línea de comandos integrada con Flask CLI para gestión completa del ciclo de vida de tokens JWT.

## Comandos Disponibles

### Generar Token

```bash
flask tokens generate \
  --issued-to "cliente-api-1" \
  --issuer "mi-servicio" \
  --type "access" \
  --notes "Descripción opcional" \
  --fresh  # Opcional: marcar como fresh token
```

### Listar Tokens

```bash
# Todos los tokens
flask tokens list

# Solo activos
flask tokens list --active-only

# Filtrar por cliente
flask tokens list --issued-to "cliente-1"

# Filtrar por issuer
flask tokens list --issuer "api-service"

# Output en JSON
flask tokens list --json
```

### Consultar Token Específico

```bash
flask tokens query --jti "<JTI_DEL_TOKEN>"
```

### Revocar Token

```bash
flask tokens revoke \
  --jti "<JTI_DEL_TOKEN>" \
  --reason "Motivo de revocación" \
  --revoked-by "admin"
```

### Restaurar Token

```bash
flask tokens unrevoke --jti "<JTI_DEL_TOKEN>"
```

### Ver Estadísticas

```bash
flask tokens stats

# Output en JSON
flask tokens stats --json
```

## Uso en Docker

```bash
# Acceder al contenedor
docker exec -it flask-middleware-dev bash

# Ejecutar comandos
flask tokens generate --issued-to "cliente" --issuer "api"
flask tokens list
flask tokens stats
```

## Requisitos

- Python 3.8+
- Flask CLI
- Variables de entorno configuradas (`.env`)
- `JWT_SECRET_KEY` debe estar definido

## Ver Documentación Completa

Consultar [../docs/authentication.md](../docs/authentication.md) para guía completa.