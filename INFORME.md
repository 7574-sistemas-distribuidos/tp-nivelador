Redactar un breve informe en donde se detallen los aspectos más importantes de la solución provista, como ser el protocolo de comunicación implementado y los mecanismos para sincronizar la ejecución concurrente.

# Protocolo

Comentar un poco mas detalles que no estén claros o expresados en los diagramas

# Batching


## Decisiones de diseño

Max Payload Bytes = 2^16 - 1 = 65535 bytes

1 Bet en Bytes representa = 18 bytes fijos + F + L siendo F y L variables que pueden tomar una cantidad aleatoria de bytes.
Pero, en realidad, sé que esa cantidad está acotada porque definí al largo de esos campos con 1 byte.

Entonces:

0 <= F <= 255

0 <= L <= 255

Esto significa que puedo guardar nombres y apellidos de una longitud máxima de 2*255 bytes.
Pero los nombres y apellidos más largos encontrados en todos los archivos son:

Max F en archivos = Milagros De Los Angeles = 23 bytes
Max L en archivos = Valenzuela = 10 bytes

Luego, mi máximo Bet en bytes observado es a lo sumo: 51 bytes.

Este umbral se encuentra muy debajo del límite de 255 bytes.

Entonces el valor máximo que podría tener BATCH_SIZE:

Max Payload Bytes // Max Umbral:

- En el dataset = 65535 // 51 = 1285 bytes
- Por el formato permitido - len de 2 bytes = 65535 // 528 = 124 bytes

Imponer la restricción / cota de 124 no parece tener mucho sentido para este conjunto de datos que rechazaría un batch de 500 que funciona bien, pero puede resultar optimista si F y L cambiaran mucho.

Elijo validar entonces el payload serializado real contra el límite real antes de escribir algo, de modo que un batch que exceda el límite falla de forma explícita.

---

Comentar el agregado de mensajes

# Concurrencia

bets.csv actua como "la base de datos" o el lugar persistente que conoce el servidor, la lotería nacional, respecto de las agencias (clientes) que envían las respuestas.
Al tener más de una agencia conectada envíandole mensajes al servidor, hay secciones que pueden sufrir problemas al ocurrir operaciones concurrentes en tiempo.
Uno de los problemas detectados es el acceso al método store_bets que maneja la lotería para poder registrar cada apuesta de cada agencia. El problema es que al haber múltiples agencias envian apuestas y un servidor intentando registrarlas, en la escritura del archivo puede ocurrir un incorrecto intercalamiento de filas resultando en una fila inavlida, con algún recorte, o con algu dato incorrecto. El problema no es el objeto lotería per sé sino el archivo al que apunta, que si es mutable y si es compartido.
Por otro lado, tengo que satisfacer la condición de que a la hora de hacer el sorteo y anunciar los ganadores, debo contar con un mínimo de agencias para realizar el sorteo. Ya tengo una separación por mensajes en cuanto a registro de apuestas y resultados ganadores, la separación entre los mismos es el mensaje finalize_bets_sending. En ese momento, cuando el servidor hace el dispatch de ese mensaje, ya cuento con toda la informacion que necesito para poder esperar a ver si cumplo con el mínimo de agencias requerido por configuración y a partir de ese momento computar el sorteo para luego notificar.
Resta entonces contar haber recibido esos mensajes para poder ejecutar esa condición, pero, ahí me aparece otra sección critica, ese contador de mensajes que puede ser modificado en el transcurso del intercambio de mensajes.

Secciones críticas identificadas:

1. store_bets abre, escribe y cierra el archivo en una sola llamada.

Con 2 hilos escribiendo en simultáneo, una fila del archivo puede partirse y otra intercalarse en el medio produciendo luego un error a la hora de desempaquetar los campos de cada fila con load_bets.
La propuesta para solucionar este problema es utilizar un lock sobre el método que permita solo a un hilo escribir a la vez.


2. espera del sorteo


El sorteo no puede realizarse hasta recibir AGENCY_QUORUM_MIN mensajes finalize_bets_sending. Esto requiere contar esos mensajes y bloquear a cada sesión que termine antes de alcanzar el mínimo.

Un contador protegido por un lock no alcanza en este caso porque entre que un hilo verifica el contador y efectivamente se duerme, otro hilo puede alcanzar el quórum y emitir la notificación que se pierde porque todavía no hay nadie escuchando. 

La propuesta es usar un condition, cuyo wait_for libera el lock y bloquea de forma atómica, eliminando esa ventana.