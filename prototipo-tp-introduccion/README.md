# TP Introductorio: Docker, Comunicaciones y Concurrencia

---

## Introducción

El objetivo de este trabajo es tanto repasar conceptos fundamentales de la concurrencia y la comunicación, como introducir a los estudiantes al desarrollo de sistemas distribuídos, en donde el código de las partes que lo componen se encapuslan en _containers_, orquestrados en este caso por la herramienta [Docker Compose](https://docs.docker.com/compose/).

Se provee un esqueleto básico de "echo server". El cliente (Golang) y el servidor (Python) fueron desarrollados en diferentes lenguajes simplemente para mostrar cómo dos lenguajes de programación pueden convivir en el mismo proyecto sin necesidad de bindings o complejas integraciones.

Los alumnos deberán resolver una guía de ejercicios incrementales, que los llevará desde un esqueleto básico de "echo server" hasta un sistema distribuído simple en donde distintas agencias de lotería cargan participantes en un servidor central, que realizará un sorteo y les informará los participantes que han ganado.

## Condiciones de Entrega

Se espera que los alumnos realicen un _fork_ del presente repositorio y que trabajen sobre el mismo en sucesivos commits siguiendo los ejercicios listados a continuación. Aquellos marcados como "_(Complementario)_" no se evaluarán, por lo que se recomienda abordarlos tras haber completado los obligatorios.

La entrega consiste en el enlace al último commit que hayan realizado, por ejemplo:

`https://github.com/7574-sistemas-distribuidos/tp-coordinacion/commit/6de10feffc3464194fc87536266f70ae1cb73fac`

Se espera que se detallen en el archivo `INFORME.md` los aspectos más importantes de la solución provista, como ser el protocolo de comunicación implementado y los mecanismos para sincronizar la ejecución concurrente.

Además se proveen pruebas automáticas de caja negra. Se exige que la resolución de los ejercicios pase tales pruebas, o en su defecto que las discrepancias sean justificadas y discutidas con los docentes antes del día de la entrega. El incumplimiento de las pruebas es condición de desaprobación, pero su cumplimiento no es suficiente para la aprobación. Se pide a los alumnos leer atentamente el enunciado y **tener en cuenta** los criterios de corrección informados [en el campus](https://campusgrado.fi.uba.ar/mod/page/view.php?id=73393).

Los cambios a archivos fuera de la carpeta `src`, incluyendo `docker-compose.yaml` y los archivos de prueba de la carpeta `input` **se revertirán** antes de ejecutar las pruebas. También se descartaran las modificaciones realizadas sobre las definiciones en archivos `Dockerfile`.

## Parte 1: Introducción a Docker

### Ejercicio N°1:

Instalar Docker Engine siguiendo la [guía de instalación oficial](https://docs.docker.com/engine/install/) para el sistema operativo y distribución correspondiente, ej.: Paso a paso para [Ubuntu](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository). En Windows y MacOs Docker Engine se distribuye dentro de la herramienta comercial Docker Desktop.

Luego, iniciar los contenedores del trabajo con `make up`. Tras la descarga de las imágenes base y la construcción de las imágenes derivadas de ellas se deberían poder ver logs de ejecución, ej.:

```bash
client_0  | 2026/06/25 19:18:21 WARN Retrying connection...
server    | 2026/06/25 19:18:21 INFO Listening to connections
server    | 2026/06/25 19:18:22 INFO A new client has connected
client_0  | 2026/06/25 19:18:22 INFO Connected to server
client_0  | 2026/06/25 19:18:22 INFO Sending message agency_id=0 message_id=0
server    | 2026/06/25 19:18:22 INFO Echoing to client agency_id=0 message_id=0
client_0  | 2026/06/25 19:18:22 INFO Received message agency_id=0 message_id=0
client_0  | 2026/06/25 19:18:23 INFO Sending message agency_id=0 message_id=1
client_0  | 2026/06/25 19:18:23 INFO Received message agency_id=0 message_id=1
server    | 2026/06/25 19:18:23 INFO Echoing to client agency_id=0 message_id=1
client_0  | 2026/06/25 19:18:24 INFO Sending message agency_id=0 message_id=2
client_0  | 2026/06/25 19:18:24 INFO Received message agency_id=0 message_id=2
server    | 2026/06/25 19:18:24 INFO Echoing to client agency_id=0 message_id=2
server    | 2026/06/25 19:18:25 INFO Client disconnected
server    | 2026/06/25 19:18:25 INFO Listening to connections
client_0 exited with code 0
```

#### Comandos básicos del Makefile

`make up` : Inicia los contenedores del sistema y comienza a seguir los logs de todos ellos en un solo flujo de salida.

`make down`: Detiene los contenedores y libera los recursos asociados.

`make logs`: Realiza un seguimiento de los logs de todos los contenedores en un solo flujo de salida.

`make test`: Inicia los contenedores del sistema, espera a que los clientes finalicen, realiza distintas pruebas para validar la implementación y detiene los contenederes.

### Ejercicio N°2

Definir en el archivo `docker-compose.yaml` más contenedores de clientes, basados en el mismo archivo `Dockerfile`. Editar sus nombres y la variable de entorno `AGENCY_ID` . Finalmente reiniciar los contenedores ejecutando `make down` y `make up`. Deberían reflejarse en los logs la ejecución de todos los clientes definidos. Las entradas de los logs pueden mezclarse debido al órden en el que se escriben en el archivo de salida de Docker, de momento el echo server no atiende a clientes concurrentemente.

### Ejercicio N°3 (Complementario)

Exponer los puertos del servidor al equipo anfitrión dentro de las definiciones del archivo `docker-compose.yaml` , de forma tal que al ejecutar `echo "Hello World" | nc localhost 5678` el proceso en el equipo anfitrión se pueda conectar con el proceso dentro de Docker y reciba el eco del mensaje enviado.

### Ejercicio N°4 (Complementario)

Crear un script de bash que sin exponer los puertos del servidor al equipo anfitrión, ni editar el archivo `docker-compose.yaml` permita verificar el correcto funcionamiento del servidor utilizando el comando `netcat` para interactuar con el mismo, como en el **Ejercicio N°3** (hint: `docker network`).

### Ejercicio N°5

Modificar el código del cliente para que en lugar de conectarse con el servidor lea la primera línea del archivo `INPUT_FILE` y la escriba en el archivo `OUTPUT_FILE`. Los cambios en los archivos de entrada deben reflejarse entre ejecuciones sin que se requiera reconstruír las imágenes de Docker. Además el archivo de salida debería persistirse por fuera del contenedor y ser accesible desde el equipo anfitrión en el directorio `output` (hint: `docker volumes`).

## Parte 2: Repaso de Comunicaciones

### Ejercicio N°6

Modificar el cliente para que lea línea a línea el archivo de entrada `INPUT_FILE` con datos de los participantes y envíe los datos de la agencia y las apuestas al servidor.

El servidor emulará la _central de Lotería Nacional_. Deberá recibir los campos de la cada apuesta desde los clientes y almacenar la información mediante el método `store_bet` de la clase `Lottery` para control futuro de ganadores.

Cuando el cliente acabe de enviar las apuestas, el servidor deberá calcular los participantes que hayan ganado mediante los métodos `load_bets` y`has_won` de la clase `Lottery` y retornar al cliente el listado de ganadores.

La clases `Lottery` y `Bet` son provistas por la cátedra y no podrán ser modificadas por el alumno.

Finalmente el cliente deberá persistir los ganadores en el archivo `OUTPUT_FILE`.

Se deberá implementar un módulo de comunicación entre el cliente y el servidor donde se maneje el envío y la recepción de los paquetes, el cual se espera que contemple:

- Definición de un protocolo para el envío de los mensajes.
- Serialización de los datos.
- Correcta separación de responsabilidades entre modelo de dominio y capa de comunicación.
- Correcto empleo de sockets, incluyendo manejo de errores y evitando los fenómenos conocidos como [_short read y short write_](https://cs61.seas.harvard.edu/site/2018/FileDescriptors/).

A partir de este ejercicio, si se ejecutase `make test` habiendo configurado un solo cliente la primera prueba debería pasar exitosamente. Además ya no se deberían utilizar las constantes `ECHO_CLIENT_*`, ni `ECHO_SERVER_*`, que solo servían de ejemplo. El grueso de ña sincronización entre cliente y servidor debe estar dada por el intercambio de mensajes, no por la espera de un lapso de tiempo prefijado.

### Ejercicio N°7

Modificar los clientes para que envíen varias apuestas dentro de un mismo mensaje. Esta modalidad es conocida como procesamiento por _chunks_ , _batchs_ o _lotes_ y permite acortar tiempos de transmisión y procesamiento a lo largo de toda la ejecución.

La cantidad máxima de apuestas dentro de cada _batch_ debe ser configurable mediante la variable de entorno `BATCH_SIZE`. Establecer un valor por defecto de modo tal que los paquetes no excedan los 8kB.

Por su parte, el servidor deberá poder comprender los nuevos mensajes y responder con éxito solamente si todas las apuestas del _batch_ fueron procesadas correctamente.

### Ejercicio N°8 (Complementario)

Modificar al servidor para que espere a la notificación de un mínimo de agencias para realizar el sorteo. Este mínimo se definirá mediante la variable de entorno `AGENCY_QUORUM_MIN`.No es correcto realizar un broadcast de todos los ganadores hacia todas las agencias, se espera que los ganadores en `OUTPUT_FILE` estén presentes en `INPUT_FILE`.

Para esto es necesario alternar la atención de los clientes, pero no se admite aún una solución basada en la concurrencia (hint: comunicación asincrónica).

## Parte 3: Repaso de Concurrencia

### Ejercicio N°9:

Modificar el servidor para que permita aceptar conexiones y procesar mensajes en concurrentemente. Deberá esperar a la notificación de un mínimo de agencias para realizar el sorteo. Este mínimo se definirá mediante la variable de entorno `AGENCY_QUORUM_MIN`. No es correcto realizar un broadcast de todos los ganadores hacia todas las agencias, se espera que los ganadores en `OUTPUT_FILE` estén presentes en `INPUT_FILE`.

En caso de que el alumno implemente el servidor en Python utilizando _multithreading_, deberán tenerse en cuenta las [limitaciones propias del lenguaje](https://wiki.python.org/moin/GlobalInterpreterLock).

### Ejercicio N°10:

Modificar servidor y cliente para que ambos sistemas terminen de forma _graceful_ al recibir la signal SIGTERM. Terminar la aplicación de forma _graceful_ implica que todos los _file descriptors_ (entre los que se encuentran archivos, sockets, ipcs, threads y procesos) deben cerrarse correctamente antes que el hilo de la aplicación principal finalice (hint: Verificar que hace el flag `-t` utilizado en el comando `docker compose down`).

Puede adoptarse un enfoque "polite" respecto a no interrumpir la comunicación abruptamente, pero dado que se trata de una señal de terminación, el tiempo de cierre del sistema no debería quedar sujeto a la respuesta de un ente externo al mismo.

Al finalizar este ejercicio deberían pasar todas las pruebas de `make test` bajo las **Condiciones de Entrega**.
