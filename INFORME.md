Redactar un breve informe en donde se detallen los aspectos más importantes de la solución provista, como ser el protocolo de comunicación implementado y los mecanismos para sincronizar la ejecución concurrente.

# Protocolo

Antes de comenzar cada implementación, construí diagramas en excalidraw de como construiría la solución, asi que todo lo repsectivo a decisiones de diseño quedaron documentadas ahí junto con el código.

En resumen, elegí utilizar un formato mostrado en clase para poder identificar la informacion que se transmite entre las agencias y la lotería. TCP es un stream, es decir, no tengo forma de saber como envíar o recibir esos mensajes. Elegí el formato TLV en donde el type es el identificador de mi mensaje, un número del 1 al 8. El len es el valor que me permite después leer el value, que para mi representa el payload de cada mensaje. Necesito contar con esta información porque el payload justamnete puede ser variable y necesito saber cuanto leer por ejemplo.

Cada agencia envía apuestas y por eso como lotería tengo que poder identificar cuando comienza ese proceso y cuando termina dado que una vez que estén todos los registros cargados, tengo que como lotería realizar un cómputo de los ganadores para esa agencia.
Para delimitar ese span de tiempo, o estado de espera de la lotería para con respecto a las apuestas, lo diseño con dos mensajes simples de aviso de inicio y finalización.

Notar que en el inicio del envio envío el id de la agencia (separado de la apuesta) para poder identificar a cada apuesta con su lugar de origen

Con el último mensaje, como lotería sé que puedo empezar a procesar y no quedarme esperando indefinidamente más mensajes por parte de las agencias.

Elijo un manejo simétrico a este funcionamiento pero desde el lado de la lotería luego para poder enviar a las apuestas ganadoras.

Conceptualmente lo que viaja es una apuesta cargada / una apuesta ganadora, por lo tanto aprovechar compartir esa estructura me ahorra tener que serializar / deserializar otra estructura y me ayuda a mantener uniformidad, que para este caso de uso, cumple.

Notar que solo viaja la apuesta, no el agency id. Cada agencia la aporta desde la sesión que viaja y los ganadores devueltos ya son los de esa agencia.

Sobre los campos: los nombres y los apellidos, al ser registros variables, fueron delimitados con un largo por delante, y el prefijo evita elegir un separador y escaparlo. birthdate de largo fijo, no lo trunco, elegí arbitrariamente ese largo porque las fechas solo pueden tener ese formato: YYYY/MM/DD.
Los nombres se validan como utf-8 al deserializar de los dos lados.

# Batching

El batching no cambió el framing ni el registro: filled_bets ya transportaba una secuencia, así que pasar de uno a N no tocó el formato. Lo que agregó fueron los dos "acks" por batch. En el caso de éxito cada batch recibe confirmación y la sesión cierra con finalize_bets_sending mientras que en caso de que haya habido algún error al procesar el batch, el mensaje de rechazo corta la sesión antes de esa marca, y por lo tanto esa agencia tampoco cuenta para el quórum.

Nota: Vale la pena decir que fue esa validación la que convirtió el bug de number en un error legible en la primera corrida: con casteo silencioso, 65536 se habría guardado como 0 y el sistema habría terminado sin fallar, con datos incorrectos en bets.csv dificilmente reconocibles.

El último lote de apuestas puede ser menor a BATCH_SIZE: la cantidad de apuestas no tiene por qué ser múltiplo, y el cliente envía el remanente como un lote más antes de finalizar.

---

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

Actualización:

Efectivamente tuve los siguientes errores que me hicieron notar el error antes que un ctaseo / truncamiento silencioso:

client_0  | 2026/09/10 13:46:13 ERROR action=send-bets result=fail bet-line=65537 err="number 65536 does not fit in 2 bytes"

client_0  | 2026/09/10 13:46:13 ERROR action=client-run result=fail err="number 65536 does not fit in 2 bytes"


El registro de apuesta serializaba number en 2 bytes, es decir un rango de 0 a 65.535. Los archivos de input provistos en base a lo explicado anteriormente no superaban esa cantidad.
La prueba de memoria usa  el índice de la fila como número de apuesta asi que ese valor ya no entra en el campo. Por eso voy a aumentar a 2 bytes el numero. Con ese cambio, los 18 bytes fijos del cálculo de batching de la sección anterior pasan a ser 20.


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

# Terminación Graceful

Al llegar SIGTERM todos los hilos (representando las sesiones de cada agencia) están bloqueados en accept, en recv o en wait_for, y una señal no desbloquea ninguna de esas llamadas por sí sola. Entonces tengo que encontrar cómo destrabar cada bloqueo desde afuera.

Hago shutdown sobre cada socket de cliente desde una lista que cada sesión registra al aceptarse y en wait_for manejo el flag sobre un quórum que ya no va a llegar.

Junto todos los threads y sockets para poder cerrarlos y desconetar desde el hilo principal.

Desde el lado del cliente hago lo mismo pero a través de una go rotuine que cierra la conexión al cancelarse el contexto (entiendo que es análogo al funcionamiento de shutdown de python).

Breve nota:

En macOS tuve el test de memoria fallando pero cuando lo corrí en mi otra computadora que tiene linux mint, el test paso sin problema (todo esto desde make test). Lo comento por las dudas, no pude identificar porque me falla en la mac.