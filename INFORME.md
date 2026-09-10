### Protocolo de comunicacion Ciente-Servidor

Se implementó un paquete que sirve para el envío de información entre las dos partes.
 
Estructura de un paquete

Cada paquete tiene un **header de 9 bytes** seguido de un payload variable:

|        Campo     | Tamaño | Descripción |
| :--- | :--- | :--- |
| `packet_type`     | 1 byte | Tipo de paquete (`REQUEST`, `RESPONSE`, `EOF`, `INIT`, `ACK`) |
| `sequence_number` | 4 bytes | Número de secuencia (big-endian) |
| `payload_size`    | 4 bytes | Tamaño del payload (big-endian) |
| `payload`         | N bytes | Datos específicos del tipo |

Se manejan distintos tipos de mensaje a lo largo de la comunicación 
 Tipos de paquete  

1. **INIT**: permite al cliente envíar su `agency_id`
2. **REQUEST**: permite al cliente envíar apuestas 
3. **EOF**: lo usan el cliente y el servidor para indicar que dejaran de enviar información
4. **RESPONSE**: permite al servidor enviar los ganadores
 
Cada uno de estos mensajes se responden con un **ACK** que confirma el delivery del mensaje cuyo  `sequence_number` coincide y saber en que estado.
El uso de `sequence_number` permite confirmar cada mensaje y detectar desincronización.

Serialización de datos

**Apuesta (`Bet`)**: cada campo se serializa con prefijo de longitud:
- Strings: 2 bytes de longitud (big-endian) + bytes UTF-8.
- Enteros: 4 bytes (big-endian).

**Batch**: agrupa múltiples apuestas en un mismo `REQUEST`:

```
[2 bytes: cantidad de apuestas]
  [2 bytes: longitud apuesta 1] [apuesta 1]
  [2 bytes: longitud apuesta 2] [apuesta 2]
  ...
```

El `BATCH_SIZE` es configurable por variable de entorno. Esto reduce la cantidad de paquetes y mejora el rendimiento sin necesidad de dividir apuestas entre paquetes.




#### Mecanismo de concurrencia 

Se usó en el servidor un mecanismo de multithreading, un hilo por cliente. 
El servidor es **I/O-bound** donde emplea el mayor tiempo realizando operaciones de lectura y escritura de archivos.
 
El servidor espera a que al menos `AGENCY_QUORUM_MIN` agencias terminen de enviar sus apuestas antes de calcular los ganadores. Se implementó con `threading.Barrier`:

```python
self.barrier = threading.Barrier(self.quorum, action=self._calculate_winners)
```

- Cada hilo llama a `barrier.wait()` al recibir el `EOF` del cliente.
- Cuando los `quorum` hilos llegan, se calcula los ganadores con las apuestas acumuladas.
- Luego todos los hilos se liberan simultáneamente y cada uno filtra sus propios ganadores por `agency_id`.

El archivo `bets.csv` es escrito por múltiples hilos, por lo que `store_bets` se protege con `threading.Lock`. El cálculo de ganadores también se hace bajo lock para evitar condiciones de carrera.

Al estar trabajando con el lenguaje Python nos enfrentamos a ciertas limitaciones.
El **Global Interpreter Lock (GIL)** de CPython impide que múltiples hilos ejecuten bytecode Python simultáneamente, eliminando el paralelismo real en tareas CPU-bound. Sin embargo, **el GIL se libera durante operaciones de E/S**
Como nuestro servidor pasa la mayor parte del tiempo bloqueado en `accept()` o `recv_all()` esperando datos de red, esperando en `barrier.wait()` a que otras agencias terminen, y otras cosas; el GIL no limita la concurrencia efectiva. La única sección CPU-intensiva es el cálculo de ganadores, que se ejecuta una sola vez por ronda y no es una operacion muy costosa. Por lo tanto, `threading` es una elección válida y eficiente para este problema.


#### SIGTERM

Docker envía `SIGTERM`, ambos procesos deben cerrar ordenadamente todos sus recursos  en un tiempo pequeño (5 segundos), y conocido teniendo como referencia el tiempo qie el docker compose tarda antes de forzar `SIGKILL`.
 
Solución
En el servidor:
El handler de `SIGTERM` llama a `shutdown()`, que hace tres cosas:
- Cerrar el socket de escucha y desbloquear `accept()`.
- Cerrar los sockets de los clientes y desbloquear sus `recv_all`.
- Abortar la barrera y desbloquear los hilos que esperan el quórum.
Finalmente se hace un join de todos los threads.

En el cliente:
En `Run()` se lanza en una goroutine y se usa `select` para escuchar dos cosas: que `Run()` termine normalmente, o que llegue `SIGTERM`. Si llega la señal, cierra el socket, fallan las funciones de lectura y escritura activas y se ejecutan los `defer` que cierran archivos.




