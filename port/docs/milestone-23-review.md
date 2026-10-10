# Revisión del hito 23

Base: main `7ca6863`; dos bloques revisados: save y reset.

Corrección: 0021 impide indexar tablas con ID de sector fuera de rango,
sin cambiar GBA. La ausencia de flash ya no deja un callback principal
NULL indefinidamente: main informa y termina antes de abrir ventana.
0022 evita el apagado de hardware RFU no inicializado en el reset host.
Limpieza central en atexit cubre salida limpia, retorno y spawner fallido.

Legibilidad/arquitectura: cambios por consumidor, sin nuevas interfaces ni
dependencias; dos harness separados con fixtures GDB explícitos. No se
cambia el formato de save ni se oculta el estado ERROR de un slot corrupto.

Datos/seguridad: saves, ROM de prueba, logs y ejecutables en build/ ignorado.
Los procesos de reset se consultan/cierran solo por la ruta exacta aislada,
comprobada libre antes de arrancar. Save original SHA-256 intacto:
`B5A41C3758763BBEC72769FAB4A2533BF2DB0B6312D93D25A695F9E4B9E02260`.
Coste de apertura única de flash; IdentifyFlash reutiliza el mapeo. Sin
coste añadido por frame en producción.

Evidencia: dos diálogos reales de save y 28 checksums; reapertura semántica;
checksum/ID inválidos y tercer save interrumpido recuperan slot completo.
Tamaño/solo lectura rechazan startup sin modificar archivos. Reset teclado
y función: un hijo, 1×, save válido, salida limpia desde cwd externo/ruta
con espacios. CreateProcess real error 2: cleanup y código 1, sin hijo.
13 suites PASS; normal sin símbolos diagnósticos; GBA compare OK.
Árbol con 22 parches idéntico en reproducción y exe recompilado:
`b55fa9c92f3f8e4b8ec83911bef75951698612cb`.

Resultado: apto para integración local. No se garantiza atomicidad de todo
el archivo ante pérdida eléctrica, fallos físicos o reset en cada byte.
El reset por función se prepara en GDB y no valida una escena concreta.
MMIO/IRQ, PPU y demás tareas siguen abiertas. No se realiza push.
