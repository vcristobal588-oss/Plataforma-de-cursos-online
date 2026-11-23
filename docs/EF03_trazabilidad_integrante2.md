# EF03 - Trazabilidad y Analisis Critico de IA (Integrante 2)

**Proyecto:** EcoTech Solutions - Plataforma de cursos online  
**Asignatura:** TI3021 - Programacion Orientada a Objeto Seguro  
**Integrante:** 2 (Seguridad, Autenticacion, Variables de Entorno y Validacion de Entradas)  
**Modulos evaluados:** `seguridad_ef03.py`, `ef03_api_segura.py`, `demo_ef03_seguridad.py`, `.env.example`

## 1. Prompts utilizados y uso de IA

| N.º | Solicitud / Prompt | Aporte de la IA | Revision y ajuste manual |
|---|---|---|---|
| 1 | "Audita el repositorio Plataforma-de-cursos-online y separa la logica de seguridad de ef03_api_segura.py para cubrir 3.1.2.I.5 a 3.1.2.I.8." | Propuesta de extraccion modular hacia `seguridad_ef03.py` manteniendo compatibilidad con el cliente API del Integrante 1. | Se conservaron las firmas de `consultar_tipo_cambio()` y `cargar_configuracion()` para no romper el flujo existente. |
| 2 | "Refuerza la sesion en memoria y la validacion de entradas contra falsificacion de objetos, timing attacks y SSRF." | Incorporacion de tokens con `secrets.token_urlsafe`, hash dummy de bcrypt, bloqueo por intentos y validacion de URL con `urlparse`. | Se agrego respaldo cuando `python-dotenv` no esta instalado y se creo `demo_ef03_seguridad.py` para pruebas offline. |

## 2. Explicacion bloque a bloque (`seguridad_ef03.py`)

1. **`cargar_configuracion()` (3.1.2.I.7):** Carga `.env` mediante `load_dotenv(override=False)` y lee usuario, hash bcrypt, URL, lista blanca de hosts y moneda destino. Ningun secreto queda en el codigo fuente.
2. **`validar_url_segura()`, `validar_credenciales()` y `validar_moneda()` (3.1.2.I.6):** Garantizan que los datos sean cadenas (`str`), sin caracteres de control (`\x00`, `\r`, `\n`), con lista blanca estricta (`^[A-Za-z]{3}$` para moneda) y dominio HTTPS autorizado.
3. **`autenticar()` y `ControlIntentos` (3.1.2.I.5):** Compara el usuario con `hmac.compare_digest` y la clave con `bcrypt.checkpw`. Si falla el usuario o el formato, ejecuta un hash dummy para evitar diferencias de tiempo de respuesta y bloquea tras 3 intentos fallidos.
4. **`Sesion`, `_RegistroSesiones`, `exigir_sesion_activa()` y `cerrar_sesion()` (3.1.2.I.8):** Emite un token aleatorio de 32 bytes registrado internamente, verifica expiracion con `time.monotonic()` y revoca la sesion al terminar.

## 3. Vulnerabilidades detectadas en el prototipo inicial y mejoras aplicadas

| Vulnerabilidad / Riesgo detectado | Como se corrigio | Justificacion tecnica |
|---|---|---|
| **Falsificacion de sesion en memoria:** El prototipo permitia crear `Sesion(usuario="x", autenticada=True)` directamente sin pasar por el login. | Se reemplazo el booleano `autenticada` por un `token` emitido solo dentro de `autenticar()` y verificado en `_SESIONES_ACTIVAS`. | Impide que codigo interno o pruebas construyan sesiones validas sin verificar credenciales. |
| **Fuga de tiempo (timing side-channel) y fuerza bruta:** Si el formato de usuario fallaba, no se ejecutaba `bcrypt.checkpw()`, revelando tiempos distintos; ademas no habia limite de intentos. | Se ejecuta `bcrypt.checkpw()` contra `HASH_DUMMY_BCRYPT` en todo rechazo y se agrego `ControlIntentos(maximo=3)`. | Iguala el costo computacional de respuestas fallidas y frena intentos automatizados de adivinacion. |
| **Posible SSRF o credenciales en URL:** Solo se validaba `startswith("https://")`, permitiendo URLs como `https://user:pass@otro-host.com`. | `validar_url_segura()` analiza con `urlparse`, rechaza `username/password` y exige que el host este en `ECOTECH_ALLOWED_HOSTS`. | Evita que una variable de entorno mal configurada envie la `X-API-Key` a un servidor no autorizado. |
| **Archivo `.env` ignorado por el script:** El repositorio ignoraba `.env` en `.gitignore`, pero el codigo no cargaba el archivo al ejecutarse. | Se integro `load_dotenv()` y se agrego `.env.example` documentado. | Facilita la configuracion local reproducible sin exponer secretos en Git. |