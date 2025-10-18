# Guía de Inicio Rápido

## Sistema de Autenticación JWT con CLI Integrado

Esta guía te ayudará a configurar y usar el sistema de autenticación JWT en 5 minutos.

## Paso 1: Instalar y Configurar

### Con Docker (Recomendado)

```bash
# Clonar y configurar
git clone <repository-url>
cd flask_middleware
cp .env.example .env

# Levantar aplicación
docker-compose -f docker-compose-dev.yml up -d --build
```

### Sin Docker

```bash
cd backend
pip install -r requirements.txt
```

## Paso 2: Generar tu Primer Token

### Con Docker

```bash
docker exec -it flask-middleware-dev flask tokens generate \
  --issued-to "mi-cliente" \
  --issuer "mi-api"
```

### Sin Docker

```bash
cd backend
flask tokens generate \
  --issued-to "mi-cliente" \
  --issuer "mi-api"
```

**Guarda el token generado**, lo necesitarás para hacer requests.

## Paso 3: Probar Autenticación

### Con curl

```bash
# Reemplaza <TOKEN> con el token generado
curl -X GET http://localhost:5000/api/v1/ \
  -H "Authorization: Bearer <TOKEN>"
```

### Respuesta Exitosa

```json
{
  "msg": "flask_middleware protected"
}
```

## Paso 4: Gestionar Tokens

### Ver todos los tokens

```bash
docker exec -it flask-middleware-dev flask tokens list
```

### Ver estadísticas

```bash
docker exec -it flask-middleware-dev flask tokens stats
```

### Revocar un token

```bash
docker exec -it flask-middleware-dev flask tokens revoke \
  --jti "<JTI_DEL_TOKEN>" \
  --reason "Ya no es necesario"
```

## Paso 5: Verificar Logs

Los logs incluyen información del cliente automáticamente:

```bash
# En Docker
docker exec -it flask-middleware-dev tail -f logs/$(date +%Y-%m-%d)-flask_middleware.log

# Sin Docker
cd backend
tail -f logs/$(date +%Y-%m-%d)-flask_middleware.log
```

Verás información como:

```
Authentication successful - Client: mi-cliente, Issuer: mi-api, JTI: a1b2c3d4...
```

## Casos de Uso Comunes

### Generar Token para Cliente Nuevo

```bash
docker exec -it flask-middleware-dev flask tokens generate \
  --issued-to "cliente-nuevo" \
  --issuer "produccion" \
  --notes "Cliente corporativo - Contrato #123"
```

### Revocar Token Comprometido

```bash
# 1. Buscar el JTI del token
docker exec -it flask-middleware-dev flask tokens list \
  --issued-to "cliente-comprometido"

# 2. Revocarlo
docker exec -it flask-middleware-dev flask tokens revoke \
  --jti "<JTI>" \
  --reason "Token comprometido"

# 3. Generar uno nuevo
docker exec -it flask-middleware-dev flask tokens generate \
  --issued-to "cliente-comprometido" \
  --issuer "produccion"
```

### Auditoría de Tokens

```bash
# Ver todos los tokens y su estado
docker exec -it flask-middleware-dev flask tokens stats

# Exportar a JSON
docker exec -it flask-middleware-dev flask tokens list --json > tokens.json
```

## Troubleshooting

### "Invalid token"

- Verifica que uses `JWT_SECRET_KEY` correcto del `.env`
- Genera un token nuevo con el CLI

### "Token has been revoked"

- El token está en la blacklist
- Genera un token nuevo o usa `unrevoke` si fue un error

### Hot-reload no funciona

- Verifica que `watchdog` esté instalado
- Reinicia el contenedor

## Documentación Completa

- **README Principal**: [README.md](../../README.md)
- **Autenticación**: [authentication.md](authentication.md)
- **CLI Tools**: [scripts/README.md](../scripts/README.md)
