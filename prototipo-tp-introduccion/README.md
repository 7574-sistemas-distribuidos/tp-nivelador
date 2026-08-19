# TP Introductorio: Docker, Comunicaciones y Concurrencia

---

## Introducción

El objetivo de este trabajo es tanto repasar conceptos fundamentales de la concurrencia y la comunicación, como introducir a los estudiantes al desarrollo de sistemas distribuídos, en donde el código de las partes que lo componen se encapsulan en _containers_, orquestados en este caso por la herramienta [Docker Compose](https://docs.docker.com/compose/).

Los alumnos deberán resolver una guía de ejercicios incrementales, que los llevará desde un esqueleto básico de "echo server" hasta un sistema distribuído simple en donde distintas agencias de lotería cargan participantes en un servidor central, que realizará el sorteo e informará los participantes que han ganado.

El cliente y servidor fueron desarrollados en Golang y Python para mostrar cómo dos lenguajes de programación pueden convivir en el mismo proyecto sin necesidad de bindings o complejas integraciones.

## Condiciones de Entrega

Se espera que los alumnos realicen un _fork_ del presente repositorio y que trabajen sobre el mismo en sucesivos commits siguiendo los ejercicios listados a continuación. Además deberán detallar en el archivo `INFORME.md` los aspectos más importantes de la solución provista, como ser el protocolo de comunicación implementado y los mecanismos para sincronizar la ejecución concurrente.

La entrega consiste en el enlace al último commit que hayan realizado, por ejemplo:
`https://github.com/7574-sistemas-distribuidos/tp-coordinacion/commit/6de10feffc3464194fc87536266f70ae1cb73fac`

Se proveen pruebas automáticas de caja negra. Se exige que la resolución de los ejercicios pase tales pruebas. En caso de existir discrepancias, estas deben ser discutidas con y aprobadas por los docentes antes del día de la entrega. El incumplimiento de las pruebas es condición de desaprobación, pero su cumplimiento no es suficiente para la aprobación. Se pide a los alumnos leer atentamente el enunciado y **tener en cuenta** los criterios de corrección informados [en el campus](https://campusgrado.fi.uba.ar/mod/page/view.php?id=73393).

Todos los cambios a archivos por fuera de la carpeta `client/src` o `server/src`, serán descartados antes de ejecutar las pruebas. Esto incluye notablemente `server/src_frozen`, `docker-compose.yaml`,`Dockerfile` y los archivos de prueba de la carpeta `input`. Se espera que la solución ofrecida pueda adaptarse a variaciones del contenido de estos archivos, siempre dentro de lo establecido en el enunciado de los ejercicios.

## Parte 1: Introducción a Docker

### Ejercicio N°0:

Instalar Docker Engine siguiendo la [guía de instalación oficial](https://docs.docker.com/engine/install/) para el sistema operativo y distribución correspondiente, ej.: Paso a paso para [Ubuntu](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository). En Windows y MacOs Docker Engine se distribuye dentro de la herramienta comercial Docker Desktop.

Luego, iniciar los contenedores del trabajo con `make up` y ver los logs de ejecución usando `make logs`:

```bash
client_0  | 2026/07/18 01:19:28 INFO action=connect-to-server result=in-progress
client_0  | 2026/07/18 01:19:28 WARN action=connect-to-server result=fail attempt=0
client_0  | 2026/07/18 01:19:28 WARN action=connect-to-server result=fail attempt=1
server    | 2026/07/18 01:19:28 INFO action=accept-connection result=in-progress 
client_0  | 2026/07/18 01:19:28 INFO action=connect-to-server result=success
client_0  | 2026/07/18 01:19:28 INFO action=test-echo-server result=in-progress agency-id=0 message-id=0
server    | 2026/07/18 01:19:28 INFO action=accept-connection result=success 
server    | 2026/07/18 01:19:28 INFO action=handle-client result=in-progress 
client_0  | 2026/07/18 01:19:29 INFO action=test-echo-server result=in-progress agency-id=0 message-id=1
client_0  | 2026/07/18 01:19:30 INFO action=test-echo-server result=in-progress agency-id=0 message-id=2
client_0  | 2026/07/18 01:19:31 INFO action=test-echo-server result=success agency-id=0
server    | 2026/07/18 01:19:31 INFO action=handle-client result=success messages-amount=3
server    | 2026/07/18 01:19:31 INFO action=accept-connection result=in-progress 
client_0 exited with code 0
```

#### Comandos básicos del Makefile

`make up` :  Descarga de las imágenes base de los servicios definidos, construye imágenes derivadas e inicia los contenedores del sistema.

`make down`: Detiene los contenedores y libera los recursos asociados.

`make logs`: Realiza un seguimiento de los logs de todos los contenedores en un solo flujo de salida.

`make test`: Realiza distintas pruebas de caja negra para garantizar que la solución cumpla con un estándar mínimo de calidad.

### Ejercicio N°1

Definir en el archivo `docker-compose.yaml` cinco contenedores de clientes, basados en el mismo archivo `Dockerfile`. Editar sus nombres y la variable de entorno `AGENCY_ID` para poder diferenciar las entradas de los logs. Finalmente reiniciar los contenedores ejecutando `make down`, seguido de `make up`.

El echo server atiende a los clientes de forma serial (no concurrente), pero aún así las entradas de los logs pueden mezclarse debido al órden en el que se escriben en el archivo de salida de Docker.

### Ejercicio N°2

Exponer los puertos del servidor al equipo anfitrión dentro de las definiciones del archivo `docker-compose.yaml`, de forma tal que al ejecutar `echo "Hello World" | nc localhost 5678` el proceso en el equipo anfitrión se pueda conectar con el proceso dentro de Docker y reciba el eco del mensaje enviado.

__Opcional:__ Crear un script de bash que permita verificar el correcto funcionamiento del servidor utilizando el comando `netcat` dentro de un contenedor sin utilizar el sistema del equipo anfitrión. Es decir, sin exponer los puertos del servidor al equipo anfitrión, ni editar el archivo `docker-compose.yaml`. (hint: `docker network`).

### Ejercicio N°3

Modificar el código del cliente para que se lea línea por línea el archivo `INPUT_FILE` y se envíen al servidor en un mensaje individual. Las respuestas del servidor deben persistirse en el archivo `OUTPUT_FILE`.

El archivo de salida deberá persistirse por fuera del contenedor del cliente y ser accesible desde el equipo anfitrión en el directorio `output`. Cualquier cambio en los archivos de entrada entre ejecuciones no debe obligar a reconstruír la imágen del cliente (hint: `docker volumes`).

## Parte 2: Repaso de Comunicaciones

### Ejercicio Nº4

Mejorar la implementación de las funciones `recv_all` y `send_all` de cliente y servidor para que se contemplen posibles errores en la comunicación y se eviten los escenarios conocidos como [_short read y short write_](https://cs61.seas.harvard.edu/site/2018/FileDescriptors/).
En Python utilizar solamente los métodos `send`y `recv` de la biblioteca `socket.socket`. En Golang utilizar solamente los métodos `Write` y`Read` de `net.Conn`.

### Ejercicio N°5

Implementar un protocolo de comunicación entre cliente y servidor en donde se maneje el envío y la recepción de los los datos de la agencia y las apuestas. Se espera que contemple:
- Correcta serialización y deserialización de los datos.
- Correcta separación de responsabilidades entre modelo de dominio y capa de comunicación.
- Correcto empleo de sockets, incluyendo manejo de errores y los escenarios de short read o short write ya descritos. 

El servidor emulará la _central de Lotería Nacional_. Deberá recibir los campos de cada apuesta desde los clientes y almacenar la información mediante el método `store_bet` de la clase `Lottery` para el futuro control de ganadores.

Cuando el cliente acabe de enviar las apuestas, el servidor deberá calcular los participantes que hayan ganado mediante los métodos `load_bets` y `has_won` de la clase `Lottery` y retornar al cliente el listado de ganadores.

Finalmente el cliente deberá persistir los ganadores en el archivo `OUTPUT_FILE`.

Eliminar las constantes `ECHO_CLIENT_*`/`ECHO_SERVER_*`. El grueso de la sincronización entre cliente y servidor debe estar dada por el intercambio de mensajes, no por la espera de un lapso de tiempo prefijado.

### Ejercicio N°6

Modificar los clientes para que envíen varias apuestas dentro de un mismo mensaje. Esta modalidad es conocida como procesamiento por _chunks_ , _batchs_ o _lotes_ y permite acortar tiempos de transmisión y procesamiento a lo largo de toda la ejecución. Por su parte, el servidor deberá poder comprender los nuevos mensajes y responder con éxito solamente si todas las apuestas del _batch_ fueron procesadas correctamente.

La cantidad de registros de apuesta dentro de cada _batch_ debe ser configurable mediante la variable de entorno `BATCH_SIZE`. No es obligatorio manejar registros de apuestas divididos entre más de un paquete; se admiten soluciones en donde se envíen tantos registros de apuesta completos como quepan en un _batch_.

## Parte 3: Repaso de Concurrencia

### Ejercicio N°7:

Modificar el servidor para que permita aceptar conexiones y procesar mensajes concurrentemente. Deberá esperar a la notificación de un mínimo de agencias para realizar el sorteo. Este mínimo se definirá mediante la variable de entorno `AGENCY_QUORUM_MIN`. No es correcto realizar un broadcast de todos los ganadores hacia todas las agencias, se espera que los ganadores en `OUTPUT_FILE` estén presentes en `INPUT_FILE`.

No se permite utilizar futures/asyncio. En caso de que el alumno utilice _multithreading_, deberán tenerse en cuenta las [limitaciones propias del lenguaje](https://wiki.python.org/moin/GlobalInterpreterLock).

### Ejercicio N°8:

Modificar servidor y cliente para que ambos sistemas terminen de forma _graceful_ al recibir la signal SIGTERM. Terminar la aplicación de forma _graceful_ implica que todos los _file descriptors_ (entre los que se encuentran archivos, sockets, ipcs, threads y procesos) deben cerrarse correctamente antes que el hilo de la aplicación principal finalice (hint: Verificar que hace el flag `-t` utilizado en el comando `docker compose down`).

Puede adoptarse un enfoque "polite" respecto a no interrumpir la comunicación abruptamente, pero dado que se trata de una señal de terminación, el tiempo de cierre del sistema deberá ser conocido y acotado.
