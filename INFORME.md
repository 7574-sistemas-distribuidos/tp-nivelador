# Informe de TP Nivelador


    Se implemento un servidor que atiende a clientes/agencias de manera concurrente, recibiendo apuestas de personas. Cuando el minimo de quorum de agencias es logrado, se cierra el sorteo y se calculan los ganadores para estas agencias. Estas van a recibir los ganadores de las apuestas que enviaron. En el caso de no llegarse al minimo de quorum, no hay sorteo.



## Protocolo de comunicación

Se implementó un protocolo binario entre cliente (GO) y servidor (Python). 

### Formato general de Mensajes

Todo mensaje tiene un header fijo de 3 bytes seguido de un payload de tamaño variable:

```
HEADER (3 bytes)
  tipo:          1 byte
  largo payload: 2 bytes (big-endian)
```
PAYLOAD (variable, tamaño = largo indicado en el header)Claramente, el largo esta limitado por el espacio en que se puede definir en el header el largo payload. 

El campo de largo permite a las funciones de lectura saber exactamente cuántos bytes leer continuación, sin depender de delimitadores ni que el payload sea fijo. 

### Tipos de mensaje

| Tipo | Id | Dirección | Descripción |
|------|-------|-----------|-------------|
| BET  | 1 | (se usa en BATCH) | una apuesta |
| WINNER | 2 | servidor → cliente | un ganador |
| ACK | 3 | ambos sentidos | confirmación, sin payload |
| END | 4 | ambos sentidos | fin de la comunicación |
| BATCH | 5 | cliente → servidor | n apuestas concatenadas |

### Codificación

**Campos de largo variable** -> nombre, apellido 
Se codifican con un prefijo de 1 byte indicando su longitud en bytes, seguido del contenido en UTF-8. El prefijo de 1 byte limita cada campo a 255 bytes.

**Campos de largo fijo** -> documento, número, fecha de nacimiento 
4 bytes cada uno, en big-endian.

**Fecha de nacimiento** -> se transforma de AAAA-MM-DD a un único entero de 4 bytes con formato AAAAMMDD 

### Batching

El payload de un mensaje BATCH contiene el agency_id (1 byte) seguido de N apuestas concatenadas, cada una codificada con el formato que describimos antes de apuesta. 
La cantidad de apuestas por batch es configurable mediante BATCH_SIZE. Además, el cliente corta el batch si el agregar una apuesta más supera el límite del protocolo (el máximo representable en los 2 bytes de largo del header). 
Esto es un limite que podria considerarse muy restrictivo, en ese caso estimo que se tendra que modificar el protocolo. 

## Flujo de comunicación

La comunicación entre cada cliente y el servidor sigue este orden:

1. El cliente se conecta al servidor.
2. Lee `INPUT_FILE` línea por línea y agrupa las apuestas según `BATCH_SIZE`.
3. Envía cada lote mediante un mensaje `BATCH`.
4. El servidor almacena las apuestas y responde con un `ACK` por cada lote procesado correctamente.
5. Cuando termina de enviar sus apuestas, el cliente envía un mensaje `END`.
6. El servidor registra la agencia y espera hasta alcanzar `AGENCY_QUORUM_MIN`.
7. El coordinador calcula los ganadores de las agencias registradas en esa ronda.
8. El servidor envía los ganadores correspondientes mediante mensajes `WINNER` y espera un `ACK` después de cada uno.
9. Cuando termina de enviar los ganadores, el servidor envía un mensaje `END`.
10. El cliente guarda los ganadores recibidos en `OUTPUT_FILE`.

 
### Separación de responsabilidades

- El módulo protocol conoce únicamente el formato de los mensajes (serialización/deserialización). 
- La lectura/escritura de bytes crudos vive en safe_socket. 
- El modelo de dominio (clase Bet, lógica de sorteo) vive en lottery (codigo de base que se recibio). 


### Manejo de short read / short write

Los módulos safe_socket (uno por cliente y otro por server) implementan la lectura y escritura sobre el socket y loopean acumulando bytes hasta completar el tamaño esperado. 

## Mecanismos de sincronización 

### Cliente

El cliente es mayormente secuencial por como es la comunicacion con el servidor (conectar → enviar apuestas → enviar END → recibir ganadores), pero necesita reaccionar a SIGTERM en cualquier punto de ese flujo para hacer el corte "gracefully" y cerrar correctamente todos los recursos, en el momento. 
Para esto se usa context.Context: una variable inmutable que al recibir la señal, se cancela un contexto compartido, y una goroutine dedicada fuerza el cierre de la conexión en el momento. Si hay una operacion de lectura o escritura, hay que forzar el cierre del socket para desbloquearla. 

### Servidor

El servidor acepta y procesa conexiones de forma concurrente usando threading. 
La justificación de por qué el GIL no es un problema: el trabajo del servidor es mas que nada I/O (esperar datos de sockets, esperar a que se junte el quórum) -> el GIL se libera durante las llamadas bloqueantes de I/O, por lo que los hilos logran paralelismo donde importa (atender múltiples conexiones simultáneamente).

Se lanza un hilo por cada conexión aceptada (_handle_client), más un hilo adicional dedicado al Coordinator.

**Sincronización del Lottery**: un Lock (lottery_lock) protege tanto la escritura de apuestas (store_bets, desde cada hilo de agencia) como la lectura para calcular ganadores (load_bets, desde el hilo del Coordinator). Asi se vitando que un sorteo lea datos a mitad de una escritura de otra agencia.

**Coordinación del quórum**: el Coordinator corre en su propio hilo, consumiendo de una Queue los registros de agencias que ya terminaron de enviar sus apuestas. Al juntar AGENCY_QUORUM_MIN agencias registradas, calcula los ganadores de esas agencias y les responde por un canal propio de cada una, para luego vaciar el registro y quedar listo para una próxima ronda. 
El servidor resuelve sorteos en grupos sucesivos de a AGENCY_QUORUM_MIN, permitiendo múltiples rondas.

**Graceful shutdown**: ante la señal SIGTERM, el servidor:
1. Marca un evento shutdown_event compartido.
2. Cierra el socket de escucha, no permite mas conexiones.
3. Fuerza el cierre de todos los sockets de clientes activos, desbloqueando cualquier recepcion o envio que este en proceso.
4. Empuja un valor sentinela SHUTDOWN, un objeto unico, al canal del Coordinator, que lo reenvía a cualquier agencia que esté esperando el quórum en ese momento.

Con respecto al valor sentinela, se me ocurrio al investigar como resolvian en ambientes distrbuidos los cierres de las Queues. Entiendo que no cambia mucho mas que usar un string, excepto el hecho de que es inconfundible. 

Por otra parte, el shutdown_event permite distinguir, en las excepciones genericas por cerrar sockets, si la excepción fue por el propio shutdown o si es un error "real". 

El objeto SHUTDOWN se usa en cambio para desbloquear los hilos que estan esperando en la Queue, sea el Coordinador mismo y los clientes esperando.


### Pruebas
La solución fue validada mediante make test, que ejecuta pruebas de serialización JSON, archivos de salida, concurrencia, batching, short read/write, finalización forzada y manejo de sigterm. 
Se entiende que eso es la prueba basica del codigo.  

## Diseño 

Para poder cumplir con la prueba de memoria se hicieron muchos cambios al cliente sobre como lee y procesa el archivo de entrada. Como, por ejemplo, leer cada registro directamente sobre bytes y evitar conversiones y copias innecesarias.

El parseo de cada apuesta se realiza usando operaciones sobre `[]byte`. 
Los valores numéricos se convierten cuando es necesario serializarlos, y los campos de texto se mantienen en bytes durante la construcción del mensaje, ya que no hacia alguna validacion sobre ellos de cualquier manera mas que chequear el largo. 

También se reutilizan buffers durante el envío. El buffer `sendBuf` del cliente conserva la capacidad alcanzada por un batch y se reutiliza en los siguientes llamados de envios de Batch, en lugar de reservar un buffer nuevo para cada lote. Del mismo modo, se reutiliza el buffer donde se codifica cada apuesta antes de incorporarla al batch.

Estas decisiones redujeron la cantidad de alocaciones y de copias de memoria, ya que en un momento no sabia exactamente que hacia disparar el problema en el test asi que fui haciendo modificaciones de mas faciles a mas complejas (en termino de cuanto codigo modificaba). El objetivo no era evitar todas las asignaciones, sino eliminar las que se repetían innecesariamente durante la lectura, codificación y envio de las apuestas.