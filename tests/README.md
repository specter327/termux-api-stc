# Pruebas

## Presentación

El subsistema de pruebas de **termux-api-stc** verifica que la librería implemente de forma correcta, consistente y reproducible los contratos definidos por su [[../specification|especificación]].

Las pruebas tienen como objetivo comprobar tanto el comportamiento interno de la librería como su correspondencia con los comandos oficiales provistos por **Termux:API**.

La ejecución de las pruebas debe producir evidencia persistente en:

```text
tests/results/
```

Cada ejecución genera un conjunto independiente de resultados identificado mediante fecha y hora UTC.

---

# Objetivos

Las pruebas de **termux-api-stc** deben permitir verificar:

1. La integridad de la API pública de la librería.
2. La correcta construcción de argumentos para los comandos de Termux:API.
3. La interpretación correcta de `stdout`, `stderr` y códigos de salida.
4. La equivalencia semántica entre interfaces síncronas y asíncronas.
5. El comportamiento ante errores.
6. El comportamiento ante timeouts y cancelaciones.
7. El ciclo de vida correcto de subprocesses.
8. El comportamiento de operaciones continuas o de streaming.
9. La compatibilidad con la versión upstream declarada por la especificación.
10. La correspondencia entre la ejecución nativa de Termux:API y la ejecución mediante **termux-api-stc**.
11. La ausencia de regresiones entre versiones de la librería.
12. La generación de evidencia suficiente para reproducir y auditar cada campaña.

---

# Principio de conformidad

Para una operación soportada, la relación esperada es:

```text
Comando oficial Termux:API
        │
        ▼
Comportamiento observado
        │
        ≈
        ▼
termux-api-stc síncrono
        │
        ≈
        ▼
termux-api-stc asíncrono
```

Salvo las normalizaciones expresamente definidas por la especificación:

```text
semántica upstream
=
semántica STC
```

La librería no debe inventar silenciosamente resultados, defaults, estados, errores o capacidades inexistentes en el upstream.

---

# Fuentes de prueba

Las pruebas pueden utilizar dos clases de entorno.

## Entorno independiente de Android

Permite ejecutar pruebas que no requieren una instalación real de Termux:API.

Ejemplos:

* validación de argumentos;
* construcción de comandos;
* parsing;
* normalización;
* excepciones;
* fake/mocked executor;
* timeouts simulados;
* cancelaciones;
* lifecycle interno;
* API pública;
* paridad sync/async;
* regresiones.

Estas pruebas deben poder ejecutarse desde entornos GNU/Linux convencionales y sistemas CI compatibles.

## Entorno Termux real

Permite ejecutar pruebas de conformidad contra una implementación real de Termux:API.

Este entorno es necesario para validar:

* disponibilidad real de comandos;
* argumentos aceptados;
* formatos reales de salida;
* códigos de retorno;
* permisos Android;
* comportamiento del companion Termux:API;
* hardware;
* efectos laterales;
* operaciones interactivas;
* streaming;
* diferencias dependientes de Android.

Estas pruebas constituyen evidencia de comportamiento observado.

---

# Clasificación de pruebas

Las pruebas se clasifican por finalidad.

## Unitarias

Verifican unidades individuales de comportamiento sin requerir Termux:API real.

```text
unit
```

Ejemplos:

* validadores;
* parsers;
* construcción de `argv`;
* normalizadores;
* clasificación de errores;
* helpers internos.

---

## Contrato

Verifican contratos públicos de la biblioteca.

```text
contract
```

Ejemplos:

* funciones exportadas;
* firmas;
* tipos;
* argumentos;
* excepciones;
* aliases documentados;
* comportamiento sync/async equivalente.

---

## Integración

Verifican la interacción entre diferentes componentes internos.

```text
integration
```

Ejemplos:

```text
wrapper
→ executor
→ parser
→ result
```

---

## Conformidad upstream

Verifican que la librería represente fielmente el comportamiento observable del comando oficial.

```text
conformance
```

La comparación básica es:

```text
Termux:API CLI
vs.
termux-api-stc
```

Estas pruebas requieren normalmente Termux real.

---

## Dispositivo

Pruebas ejecutadas sobre Android/Termux real.

```text
device
```

Pueden depender de:

* hardware;
* permisos;
* versión Android;
* configuración;
* interacción humana.

---

## Interactivas

Requieren una acción explícita del operador.

```text
interactive
```

Por ejemplo:

* fingerprint;
* dialogs;
* SAF;
* biometric interaction;
* selección de archivos;
* interacción visual.

No deben ejecutarse automáticamente salvo solicitud explícita.

---

## Con efectos laterales

Modifican estado del dispositivo o producen una acción externa.

```text
side_effect
```

Ejemplos:

* cambiar brillo;
* modificar volumen;
* vibrar;
* crear notificaciones;
* tomar fotografías;
* modificar clipboard.

---

## Destructivas o sensibles

Pueden provocar cambios significativos, comunicaciones externas o eliminación de información.

```text
destructive
```

Ejemplos:

* SMS;
* llamadas;
* eliminación de contenido;
* operaciones sobre keystore;
* modificaciones persistentes.

Estas pruebas deben permanecer deshabilitadas por defecto.

---

# Política de ejecución

La ejecución estándar se realiza mediante:

```shell
./run-tests.sh
```

El runner debe ejecutar por defecto únicamente las pruebas que puedan realizarse de manera segura y no destructiva.

Las pruebas:

```text
interactive
side_effect
destructive
```

deben requerir activación explícita cuando corresponda.

---

# Resultados

Cada campaña debe generar resultados dentro de:

```text
tests/results/
```

El nombre de cada campaña utiliza un timestamp UTC:

```text
YYYYMMDDTHHMMSSZ
```

Ejemplo:

```text
tests/results/20260904T152530Z/
```

Cada ejecución constituye una unidad independiente de evidencia.

---

# Estructura de resultados

Una campaña debería producir como mínimo:

```text
results/
└── 20260904T152530Z/
    ├── environment.txt
    ├── metadata.txt
    ├── packages.txt
    ├── test-output.txt
    ├── exit-code.txt
    └── SHA256SUMS
```

Cuando existan pruebas de dispositivo también podrán generarse:

```text
termux-environment.txt
termux-api-commands.txt
permissions.txt
device.txt
observations/
artifacts/
```

---

# `metadata.txt`

Registra información de la campaña.

Debe incluir cuando sea posible:

```text
UTC timestamp
working directory
Git commit
Git branch
Git status
runner version
test command
```

El estado Git es importante.

Una prueba ejecutada sobre un árbol modificado:

```text
git status != clean
```

es válida como evidencia experimental, pero el commit por sí solo no identifica exactamente el código probado.

---

# `environment.txt`

Registra el entorno de ejecución.

Como mínimo:

```text
uname
operating system
architecture
Python executable
Python version
pip version
pytest version
current user
shell
```

En Termux debe registrar además, cuando sea posible:

```text
PREFIX
TERMUX_VERSION
Android version
Android API level
device manufacturer
device model
device architecture
```

---

# `packages.txt`

Debe registrar el entorno Python utilizado:

```shell
python -m pip freeze
```

Esto permite reconstruir las dependencias utilizadas durante la campaña.

---

# Información Termux:API

Cuando las pruebas se ejecuten dentro de Termux, la campaña debe intentar registrar:

```text
versión de Termux
versión del paquete termux-api
versión de la aplicación Termux:API
comandos termux-* disponibles
```

La ausencia de alguno de estos datos debe registrarse como:

```text
UNKNOWN
```

y no inferirse.

---

# Salida completa

Toda la salida de la campaña debe almacenarse sin truncamiento en:

```text
test-output.txt
```

El mismo contenido puede mostrarse simultáneamente en terminal.

La salida debe contener tanto:

```text
stdout
```

como:

```text
stderr
```

---

# Código de salida

El código final debe conservarse en:

```text
exit-code.txt
```

Valores esperados:

```text
0
```

cuando la campaña completa pasa.

Cualquier otro valor debe conservarse exactamente.

El runner debe finalizar usando el mismo código de salida de la campaña de pruebas.

---

# Integridad de evidencia

Después de generar todos los archivos de una campaña se debe calcular:

```text
SHA256SUMS
```

Ejemplo:

```shell
sha256sum metadata.txt environment.txt packages.txt test-output.txt exit-code.txt > SHA256SUMS
```

La verificación posterior se realiza mediante:

```shell
sha256sum -c SHA256SUMS
```

Los hashes deben generarse únicamente después de finalizar la escritura de los archivos correspondientes.

---

# Reproducibilidad

Una evidencia completa debe permitir responder:

```text
¿Qué código fue probado?
¿En qué commit?
¿Estaba el árbol limpio?
¿Qué versión de Python fue utilizada?
¿Qué dependencias estaban instaladas?
¿En qué sistema se ejecutó?
¿Qué versión de Termux:API estaba disponible?
¿Qué pruebas fueron ejecutadas?
¿Qué produjo cada prueba?
¿Cuál fue el código de salida?
```

Si alguno de estos datos no puede determinarse, debe registrarse explícitamente como desconocido.

---

# Pruebas sobre hardware real

Las pruebas de dispositivo deben identificar las condiciones bajo las que se ejecutaron.

Ejemplo:

```text
Device:
  Manufacturer: ...
  Model: ...
  Android: ...
  API level: ...

Termux:
  Version: ...
  Source: ...

Termux:API:
  Application version: ...
  Package version: ...

Permissions:
  Camera: granted
  Location: granted
  Microphone: denied
```

Un resultado de dispositivo no debe generalizarse automáticamente a todas las versiones de Android o hardware.

Representa comportamiento observado en el entorno registrado.

---

# Estados de prueba

Las pruebas deben distinguir al menos:

```text
PASS
FAIL
SKIP
XFAIL
ERROR
```

En pruebas dependientes de capacidades también puede ser necesario distinguir conceptualmente:

```text
UNAVAILABLE
PERMISSION_REQUIRED
UNSUPPORTED
```

Estos estados no deben convertirse automáticamente en `FAIL` si la especificación establece que la capacidad es opcional o dependiente del entorno.

---

# Ausencia de una capacidad

La inexistencia de hardware, permisos o comandos debe tratarse de acuerdo con la naturaleza de la prueba.

Ejemplo:

```text
camera hardware unavailable
```

no demuestra necesariamente un defecto en:

```text
termux-api-stc.camera
```

Por el contrario:

```text
camera available
permission granted
official CLI succeeds
STC fails
```

constituye una posible no conformidad de la librería.

---

# Comparación directa con upstream

Para capacidades importantes se utilizará una metodología de tres pasos:

```text
1. Ejecutar comando oficial.
2. Ejecutar API STC síncrona.
3. Ejecutar API STC asíncrona.
```

Se compararán:

```text
argumentos
stdout
stderr
exit status
resultado interpretado
efecto observado
```

Las diferencias intencionales deben estar documentadas en la especificación.

---

# Resultados históricos

Los archivos de:

```text
tests/results/
```

son evidencia de campañas anteriores.

No representan por sí mismos el estado actual de la librería.

Cada resultado debe interpretarse junto con su:

```text
timestamp
Git commit
Git status
environment
dependency set
```

---

# Criterio de conformidad

Una versión de **termux-api-stc** podrá declararse conforme con una versión determinada de Termux:API únicamente cuando la matriz de operaciones aplicable haya sido ejecutada y documentada bajo los criterios establecidos por la especificación.

No se asumirá compatibilidad únicamente porque:

```text
el comando existe
```

o:

```text
una llamada simple funciona
```

La conformidad debe estar respaldada por evidencia reproducible.
