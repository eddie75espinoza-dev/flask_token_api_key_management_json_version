# Guía de Autenticación JWT

## Descripción General

Este sistema implementa autenticación JWT flexible que permite múltiples clientes con capacidad de revocación selectiva sin base de datos.

### Características Principales

- **Autenticación JWT Flexible**: Acepta cualquier JWT firmado con `JWT_SECRET_KEY`
- **Múltiples Clientes**: Soporte para múltiples API_KEYs sin límite hardcodeado
- **Revocación Selectiva**: Revoca tokens individuales sin afectar otros
- **Sin Base de Datos**: Usa archivos JSON para blacklist y registro
- **Hot-Reload**: Detección automática de cambios en blacklist
- **Identificación de Clientes**: Logs detallados con información del cliente
- **CLI Completo**: Herramienta de línea de comandos para gestión

---

## Tabla de Contenidos

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Flujo de Autenticación](#flujo-de-autenticación)
3. [Generar Tokens JWT](#generar-tokens-jwt)
4. [Usar Tokens en Requests](#usar-tokens-en-requests)
5. [Gestión de Tokens con CLI](#gestión-de-tokens-con-cli)
6. [Revocar Tokens](#revocar-tokens)
7. [Archivos de Datos](#archivos-de-datos)
8. [Seguridad](#seguridad)
9. [Troubleshooting](#troubleshooting)

---

## Arquitectura del Sistema

### Componentes

```
backend/
├── core/
│   ├── middleware.py          # Decorador @token_required
│   ├── token_blacklist.py     # Sistema de revocación
│   └── token_registry.py      # Registro de tokens emitidos
├── data/
│   ├── revoked_tokens.json    # Blacklist de JTIs revocados
│   └── token_registry.json    # Registro de todos los tokens
└── scripts/
    └── token_cli.py           # CLI para gestión de tokens
```

### Métodos del TokenRegistry

El `TokenRegistry` proporciona los siguientes métodos:

- `register_token()` - Registrar un nuevo token
- `get_by_jti(jti)` - Obtener token por JTI
- `get_by_issued_to(subject)` - Obtener tokens por sujeto
- `get_by_issuer(issuer)` - Obtener tokens por emisor
- `search_tokens()` - Buscar tokens con filtros
- `mark_inactive(jti)` - Marcar token como inactivo
- `get_statistics()` - Obtener estadísticas del registro
- `count_tokens()` - Contar total de tokens

### Flujo de Datos

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Cliente   │─────>│  Middleware  │─────>│  Endpoint   │
│  (API_KEY)  │      │   JWT Auth   │      │  Protegido  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ├─> Validar firma JWT
                            ├─> Verificar blacklist
                            └─> Extraer client_info
```

---

## Flujo de Autenticación

### Paso a Paso

1. **Cliente envía request** con header `Authorization: Bearer <JWT_TOKEN>`

2. **Middleware extrae token** del header

3. **Valida firma JWT** usando `JWT_SECRET_KEY`

4. **Verifica campos requeridos**:
   - `sub` (subject): Identificador del cliente
   - `iss` (issuer): Quién emitió el token
   - `iat` (issued at): Timestamp de emisión
   - `type`: Tipo de token
   - `jti` (JWT ID): Identificador único del token

5. **Consulta blacklist** para verificar si el JTI está revocado

6. **Extrae información del cliente** y la almacena en `g.client_info`

7. **Permite acceso** o **rechaza con error apropiado**

### Códigos de Respuesta

| Código | Mensaje | Descripción |
|--------|---------|-------------|
| 200 | Success | Autenticación exitosa |
| 401 | Authorization required | Header Authorization faltante |
| 401 | Invalid authorization format | Formato de header inválido |
| 403 | Invalid token | JWT inválido o mal firmado |
| 403 | Token has been revoked | Token en blacklist |
| 500 | Authentication error | Error interno del servidor |

---

## Generar Tokens JWT

### Método 1: Usar el CLI (Recomendado)

```bash
cd backend

# Generar token para un cliente
flask tokens generate \
  --issued-to "cliente-api-1" \
  --issuer "mi-servicio" \
  --type "access" \
  --notes "Token para cliente de producción"
```

**Salida:**
```
Token generated successfully!

JTI:        a1b2c3d4-5678-90ab-cdef-1234567890ab
Issued To:  cliente-api-1
Issuer:     mi-servicio
Type:       access
Issued At:  2025-10-17T10:30:00

Token:
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTcyOT...
```
---

## Usar Tokens en Requests

### Con curl

```bash
# Definir el token
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# Hacer request
curl -X GET http://localhost:5000/api/v1/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

### Con Python (requests)

```python
import requests

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.get(
    "http://localhost:5000/api/v1/",
    headers=headers
)

print(response.json())
```

### Con JavaScript (fetch)

```javascript
const token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...";

fetch("http://localhost:5000/api/v1/", {
  method: "GET",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## Gestión de Tokens con CLI

### Comandos Disponibles

#### 1. Generar Token

```bash
# Generar token básico
flask tokens generate \
  --issued-to "cliente-1" \
  --issuer "api-service"

# Generar token con opciones adicionales
flask tokens generate \
  --issued-to "cliente-1" \
  --issuer "api-service" \
  --type "access" \
  --notes "Token para cliente de desarrollo" \
  --fresh

# Generar token con output JSON
flask tokens generate \
  --issued-to "cliente-1" \
  --issuer "api-service" \
  --json
```

#### 2. Listar Tokens

```bash
# Listar todos los tokens
flask tokens list

# Solo tokens activos
flask tokens list --active-only

# Filtrar por cliente (issued-to)
flask tokens list --issued-to "cliente-test"

# Filtrar por emisor (issuer)
flask tokens list --issuer "servicio-test"

# Combinar filtros
flask tokens list --issued-to "cliente-test" --issuer "servicio-test" --active-only

# Output en formato JSON
flask tokens list --json
```

#### 3. Consultar Token Específico

```bash
# Consultar token por JTI
flask tokens query \
  --jti "06c0712f-ea4c-4ef3-b7b2-8254bacfae23"

# Consultar con output JSON
flask tokens query \
  --jti "06c0712f-ea4c-4ef3-b7b2-8254bacfae23" \
  --json
```

#### 4. Revocar Token

```bash
flask tokens revoke \
  --jti "06c0712f-ea4c-4ef3-b7b2-8254bacfae23" \
  --reason "Compromiso de seguridad" \
  --revoked-by "admin"
```

#### 5. Comando Unrevoke (No Disponible)

**Nota**: El comando `unrevoke` ha sido eliminado porque no funciona correctamente. Los tokens revocados permanecen en el blacklist para seguridad.

#### 6. Ver Estadísticas

```bash
# Vista formateada con estadísticas completas
flask tokens stats

# Output en formato JSON
flask tokens stats --json
```

**Las estadísticas incluyen**:
- Total de tokens emitidos
- Tokens activos vs inactivos
- Número de emisores únicos
- Número de sujetos únicos
- Tokens revocados en blacklist

---

## Revocar Tokens

### Opción 1: Con CLI (Recomendado)

```bash
flask tokens revoke \
  --jti "<JTI_DEL_TOKEN>" \
  --reason "Token comprometido" \
  --revoked-by "admin"
```

### Opción 2: Editar Manualmente

Editar `backend/data/revoked_tokens.json`:

```json
{
  "revoked_jtis": [
    "jti-a-revocar-1",
    "jti-a-revocar-2"
  ],
  "last_updated": "2025-10-17T10:30:00",
  "revocations": [
    {
      "jti": "jti-a-revocar-1",
      "revoked_at": "2025-10-17T10:30:00",
      "reason": "Compromiso de seguridad",
      "issued_to": "cliente-1",
      "revoked_by": "admin"
    }
  ]
}
```

**Hot-Reload**: Los cambios se detectan automáticamente sin reiniciar.

### Opción 3: Endpoint Administrativo (Futuro)

```bash
POST /api/v1/admin/revoke
{
  "jti": "token-id-to-revoke",
  "reason": "Security breach"
}
```

---

## Archivos de Datos

### token_registry.json

Registro de todos los tokens emitidos con metadata completa.

```json
{
  "tokens": [
    {
      "jti": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "issued_to": "cliente-api-1",
      "issuer": "mi-servicio",
      "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "secret_key_hash": "abc12345...def67890",
      "algorithm": "HS256",
      "issued_at": "2025-10-17T10:30:00",
      "not_before": "2025-10-17T10:30:00",
      "expires_at": null,
      "token_type": "access",
      "additional_claims": {"fresh": false},
      "notes": "Token para producción",
      "registered_at": "2025-10-17T10:30:00",
      "is_active": true
    }
  ],
  "last_updated": "2025-10-17T10:30:00",
  "total_issued": 1
}
```

### revoked_tokens.json

Blacklist de tokens revocados.

```json
{
  "revoked_jtis": [
    "jti-revocado-1",
    "jti-revocado-2"
  ],
  "last_updated": "2025-10-17T11:00:00",
  "revocations": [
    {
      "jti": "jti-revocado-1",
      "revoked_at": "2025-10-17T11:00:00",
      "reason": "Token comprometido",
      "issued_to": "cliente-sospechoso",
      "revoked_by": "security-team"
    }
  ]
}
```

---

## Seguridad

### Mejores Prácticas

1. **JWT_SECRET_KEY Fuerte**
   ```bash
   # Generar clave segura
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Nunca Commitear .env**
   ```bash
   # Verificar que esté en .gitignore
   grep "\.env$" .gitignore
   ```

3. **Rotar Tokens Regularmente**
   ```bash
   # Generar nuevo token cada 90 días
   flask tokens generate --issued-to "cliente" --issuer "api"
   
   # Revocar token antiguo
   flask tokens revoke --jti "<OLD_JTI>" --reason "Rotación programada"
   ```

4. **Monitorear Logs**
   ```bash
   # Ver autenticaciones exitosas
   grep "Authentication successful" backend/logs/*.log
   
   # Ver intentos fallidos
   grep "Authentication failed" backend/logs/*.log
   ```

5. **Limitar Alcance de Tokens**
   - Usar `sub` descriptivo (ej: `api-analytics`, `service-billing`)
   - Documentar qué servicios usan cada token

### Información en Logs

Los logs incluyen identificación del cliente:

```json
{
  "request_id": "uuid-request",
  "method": "GET",
  "url": "http://localhost:5000/api/v1/",
  "client": {
    "sub": "cliente-api-1",
    "iss": "mi-servicio",
    "jti": "a1b2c3d4-5678-90ab-cdef-1234567890ab"
  }
}
```

---

## Troubleshooting

### Error: "Invalid token"

**Causa**: JWT no firmado correctamente o clave incorrecta.

**Solución**:
```bash
# Verificar que uses JWT_SECRET_KEY del .env
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('JWT_SECRET_KEY'))"

# Generar token nuevo con CLI
flask tokens generate --issued-to "test" --issuer "test"
```

### Error: "Token has been revoked"

**Causa**: Token está en la blacklist.

**Solución**:
```bash
# Ver tokens revocados
flask tokens stats

# Restaurar token si fue error
flask tokens unrevoke --jti "<JTI>"

# O generar token nuevo
flask tokens generate --issued-to "cliente" --issuer "api"
```

### Error: "Missing required JWT claims"

**Causa**: Token no tiene campos obligatorios (`sub`, `iss`, `iat`, `type`).

**Solución**:
```bash
# Usar CLI que genera estructura correcta
flask tokens generate --issued-to "cliente" --issuer "api"
```

### Hot-Reload No Funciona

**Causa**: `watchdog` no instalado o permisos de archivo.

**Solución**:
```bash
# Instalar watchdog
pip install watchdog

# Verificar permisos
ls -la backend/data/revoked_tokens.json

# Reiniciar aplicación
docker-compose -f docker-compose-dev.yml restart
```

### Ver Tokens de un Cliente

```bash
# Por cliente (sub)
flask tokens list --issued-to "cliente-1"

# Por issuer
flask tokens list --issuer "api-service"

# Consultar token específico
flask tokens query --jti "<JTI>"
```

---

## Recursos Adicionales

- [JWT.io](https://jwt.io/) - Debugger de JWT tokens
- [RFC 7519](https://tools.ietf.org/html/rfc7519) - Especificación JWT
- [Flask Documentation](https://flask.palletsprojects.com/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)

---

## Ejemplos Prácticos

### Caso 1: Agregar Nuevo Cliente

```bash
# 1. Generar token
flask tokens generate \
  --issued-to "nuevo-cliente-xyz" \
  --issuer "api-produccion" \
  --notes "Cliente corporativo - Contrato #12345"

# 2. Copiar el token generado
# 3. Enviar al cliente de forma segura
# 4. Cliente usa token en sus requests
```

### Caso 2: Token Comprometido

```bash
# 1. Revocar token inmediatamente
flask tokens revoke \
  --jti "<JTI_COMPROMETIDO>" \
  --reason "Token expuesto en repositorio público" \
  --revoked-by "security-team"

# 2. Generar token nuevo
flask tokens generate \
  --issued-to "cliente-afectado" \
  --issuer "api-produccion" \
  --notes "Token de reemplazo - incidente #2025-001"

# 3. Notificar al cliente con nuevo token
```

### Caso 3: Auditoría de Seguridad

```bash
# Ver todos los tokens
flask tokens list --json > audit_tokens.json

# Ver estadísticas
flask tokens stats

# Ver tokens revocados
flask tokens stats --json | jq '.blacklist'

# Ver tokens de cliente específico
flask tokens list --issued-to "cliente-sospechoso"
```

---

**Última actualización**: 2025-10-17
**Versión**: 2.0.0

