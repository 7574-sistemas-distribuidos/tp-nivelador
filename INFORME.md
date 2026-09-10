Redactar un breve informe en donde se detallen los aspectos más importantes de la solución provista, como ser el protocolo de comunicación implementado y los mecanismos para sincronizar la ejecución concurrente.

# Protocolo

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

