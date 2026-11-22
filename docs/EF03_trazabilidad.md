# EF03 - Trazabilidad y analisis de uso de IA

**Proyecto:** EcoTech Solutions - Plataforma de cursos online  
**Asignatura:** TI3021 - Programacion Orientada a Objeto Seguro  
**Integrante:** 1 (consumo de API externa, JSON, errores de red/HTTP y flujo de acceso seguro)  
**Archivo evaluado:** `ef03_api_segura.py`

## 1. Registro de prompts y aportes de IA

| N.º | Prompt / solicitud | Uso que se le dio a la IA | Resultado |
|---|---|---|---|
| 1 | "Actua como programador Python y construye el avance de la EF03 de EcoTech Solutions..." | Borrador inicial de la estructura: autenticacion, sesion, consulta HTTP, extraccion de JSON y manejo de errores. | Script base de un solo archivo, sin capas ni dependencias innecesarias. |
| 2 | "Cumple los criterios 3.1.1.I.1 a 3.1.4.I.16 de forma simple y directa." | Verificacion de cobertura criterio por criterio y ajuste de comentarios/trazabilidad. | Mapa de criterios y docstring con el flujo completo. |
| 3 | "No agregues funcionalidades extra ni arquitecturas complejas." | Poda del alcance: se descarto base de datos, registro de usuarios, reintentos automaticos y menu interactivo. | Un solo flujo: configurar -> autenticar -> validar moneda -> consultar API -> mostrar resultado. |
| 4 | "Revisa errores, redundancias o vulnerabilidades." | Analisis de riesgos y refactorizacion. | Cambios indicados en la seccion 4. |

La IA se uso como apoyo para generar el borrador, proponer nombres de funciones, redactar mensajes de error y detectar riesgos. La seleccion final del alcance, la API, las validaciones y la ejecucion de pruebas fueron revisadas manualmente.

## 2. Mapa de criterios

| Criterio | Donde se cumple |
|---|---|
| 3.1.1.I.1 | `consultar_tipo_cambio()` usa `requests.get()` contra `open.er-api.com`. |
| 3.1.1.I.2 | `respuesta.json()` convierte el cuerpo JSON a un `dict` de Python. |
| 3.1.1.I.3 | `extraer_tipo_cambio()` devuelve solo un `TipoCambio` (origen, destino, tasa, fecha); no se arrastra el JSON completo. |
| 3.1.1.I.4 | Se verifican `result`, `base_code`, `rates`, tipo numerico de la tasa, que sea finita/positiva y que la marca de tiempo sea valida. |
| 3.1.2.I.5 | `autenticar()` compara la clave con `bcrypt.checkpw()` contra un hash; nunca se guarda la contrasena en texto plano. |
| 3.1.2.I.6 | `validar_credenciales()` y `validar_moneda()` aplican listas blancas con expresiones regulares y normalizan la entrada. |
| 3.1.2.I.7 | `cargar_configuracion()` lee usuario, hash, URL, API key y moneda desde variables de entorno. |
| 3.1.2.I.8 | `consultar_tipo_cambio()` exige un objeto `Sesion` y llama a `exigir_sesion_activa()` antes de consultar. |
| 3.1.3.I.9 | Excepciones propias (`ErrorConfiguracion`, `ErrorAutenticacion`, `ErrorSesion`, `ErrorValidacion`, `ErrorApi`) y `try/except` especificos. |
| 3.1.3.I.10 | `timeout=(3.05, 5)` y captura de `Timeout`, `SSLError` y `ConnectionError`. |
| 3.1.3.I.11 | `_mensaje_http()` traduce 400, 401, 403, 404, 408, 429 y errores 5xx. |
| 3.1.3.I.12 | `main()` captura cada familia de error, muestra un mensaje seguro y devuelve un codigo de salida sin traceback. |
| 3.1.4.I.13 | Este documento y el bloque de trazabilidad del docstring del script. |
| 3.1.4.I.14 | Explicacion bloque por bloque en la respuesta de entrega y comentarios en el codigo. |
| 3.1.4.I.15 | Seccion 4: riesgos detectados. |
| 3.1.4.I.16 | Seccion 4: mejoras y justificacion tecnica. |

## 3. Revision humana

- Se probo la API real con `USD` y `CLP`: respuesta HTTP 200 y tasa obtenida correctamente.
- Se probaron credenciales correctas e incorrectas: ambas fallas devuelven el mismo mensaje generico.
- Se probaron entradas vacias, con espacios y con caracteres invalidos en la moneda: se rechazan antes de construir la URL.
- Se probo el vencimiento de sesion: `consultar_tipo_cambio()` se detiene con `ErrorSesion`.
- Se reviso que ningun secreto quede escrito en el archivo `.py`.

## 4. Riesgos detectados, mejoras aplicadas y justificacion

| Riesgo o redundancia detectada | Mejora aplicada | Justificacion tecnica |
|---|---|---|
| URL y API key podian quedar escritas en el codigo. | Se leen desde `ECOTECH_API_URL` y `ECOTECH_API_KEY`. | Evita filtrar configuracion en el repositorio y permite cambiar de proveedor sin editar el script. |
| Contrasena en texto plano. | Se guarda solo un hash bcrypt en `ECOTECH_USER_HASH`; la clave se pide con `getpass`. | bcrypt incorpora salt y costo computacional; `getpass` evita mostrar la clave en pantalla. |
| Un `except Exception` generico ocultaba errores. | Se capturan excepciones concretas y se usan excepciones propias. | Permite distinguir configuracion, autenticacion, validacion, sesion y API; los errores de programacion no se silencian. |
| Una consulta HTTP podia quedar colgada. | `timeout=(3.05, 5)`. | Limita el tiempo de conexion y de lectura; el flujo continua con un mensaje claro. |
| Se imprimian detalles tecnicos de la excepcion. | Mensajes seguros para el usuario y `raise ... from error` solo para conservar la causa interna. | Evita exponer rutas, URLs internas, claves o trazas; la causa queda disponible para depuracion. |
| El JSON completo se propagaba por el programa. | Se extrae solo `TipoCambio`. | Reduce acoplamiento con el proveedor y datos innecesarios en memoria. |
| `bool` podia pasar como numero porque `bool` hereda de `int`. | Se excluye explicitamente con `isinstance(tasa, bool)`. | Evita aceptar `True`/`False` como una tasa valida. |
| Entradas con espacios, minusculas o simbolos llegaban a la URL. | Lista blanca `^[A-Za-z]{3}$`, `strip()` y `upper()`. | Solo se permite una moneda de tres letras; se bloquean intentos de manipulacion de la ruta. |
| Mensajes distintos permitian enumerar usuarios. | Un unico mensaje "Usuario o contrasena incorrectos." y bcrypt se ejecuta aunque el usuario no coincida (cuando el formato es valido). | Reduce la fuga de informacion y la diferencia de tiempos entre usuario existente e inexistente. |
| La sesion no tenia vencimiento ni marca de autenticacion. | `Sesion.activa()` exige `autenticada=True` y usa `time.monotonic()` con `DURACION_SESION`. | Una sesion creada a mano queda inactiva por defecto; `monotonic()` no retrocede si cambia el reloj del sistema. |
| Se podia usar HTTP sin cifrado. | `cargar_configuracion()` exige que `ECOTECH_API_URL` comience con `https://`. | Protege la consulta y la API key en transito. |
| Una redireccion podia enviar la API key a otro destino. | `allow_redirects=False` y mensaje seguro para codigos 3xx. | La consulta no cambia de host de forma silenciosa. |
| La API podia responder 200 con un cuerpo que no fuera JSON. | Se captura `ValueError` al llamar a `respuesta.json()`. | Convierte un fallo de formato en un `ErrorApi` controlado. |

## 5. Riesgos residuales (declarados, no ocultos)

- La sesion vive en memoria y puede ser construida por otro codigo del mismo proceso. En produccion corresponderia un token firmado y validado en el servidor.
- Las variables de entorno pueden ser leidas por procesos con los mismos permisos del usuario; en produccion se recomienda un gestor de secretos.
- No se implementaron reintentos ni backoff: un 429 o un fallo de red se informa y el programa termina de forma controlada. Se priorizo la simplicidad del prototipo.
- El host de la API se toma de una variable de entorno confiable. En produccion conviene una lista blanca de dominios para evitar SSRF si la configuracion fuera modificable por un usuario.
- No hay registro/alta de usuarios ni almacenamiento persistente: el alcance es una demostracion de autenticacion y consumo seguro.
- El hash de demostracion que se comparta en la documentacion debe regenerarse para una entrega real.

## 6. Evidencia de ejecucion

```text
config: integrante1 CLP https://open.er-api.com/v6/latest
sesion activa: True
auth rechazada: Usuario o contrasena incorrectos.
usuario rechazado: Usuario o contrasena incorrectos.
moneda normalizada: USD
moneda invalida: La moneda debe tener exactamente 3 letras (ej: USD).
resultado: TipoCambio(origen='USD', destino='CLP', tasa=1007.791135, ...)
formato: 1 USD = 1007.7911 CLP
```

Comandos de verificacion:

```bash
python -m compileall -q ef03_api_segura.py
python ef03_api_segura.py
```
