# Revisión de la base y reproducción — hito 21

Fecha: 2026-10-10. Base main local/remota: `07207e9`. Cadena revisada:
hitos 7–20 hasta `1f83350`, más la separación de ejecutables diagnósticos.
Main es ancestro; la integración puede realizarse mediante fast-forward.

## Resultado de revisión

| Eje | Resultado |
| --- | --- |
| Corrección | 13 suites PASS; salida de casa sin combate con el binario normal; batalla controlada en Ruta 101; compare GBA OK |
| Legibilidad | Código host en módulos port; consumidores upstream conservados como parches numerados |
| Arquitectura | PORT_PC protege la conducta GBA; datos y fuentes upstream permanecen ignorados |
| Seguridad de archivos | Tests con ROM/save aislados; diagnóstico con save propio; original intacto |
| Rendimiento | Regresiones aceleradas sin ventana; las mediciones anteriores siguen documentadas, sin extrapolarlas a compatibilidad completa |

Hallazgos corregidos durante la revisión:

- Las ventanas normal y diagnóstica tenían el mismo título. Ahora la segunda
  está identificada y las pruebas GDB no muestran ventanas.
- Abrir el diagnóstico directamente podía usar el save normal. Ahora tiene
  nombre propio y un centinela verifica que la regresión no toca el normal.
- El fixture de batalla se preparaba en Villa Raíz. Ahora comprueba la
  salida de casa y carga Ruta 101 antes de iniciar la pelea controlada.
- Una tubería fallida podía dejar un objeto parcial, que make reutilizaba
  al repetir el build. Se añade `.DELETE_ON_ERROR` para eliminar el objetivo
  fallido. Los objetos del checkout de prueba se recompilaron desde cero.

Limitaciones pendientes, sin confundirlas con regresiones nuevas: IRQ de
timer, líneas de VBlank completas, bitmap, RTC, precisión de audio y enlace.
El aviso de descompresión se diagnosticó como el consumidor de la imagen
sin comprimir del entrenador; requiere el incremento separado T04. Las
funciones reales y aproximaciones están inventariadas en el plan operativo.
Los documentos BIOS antiguos también requieren actualización al estado
actual de audio y reset. No se afirma compatibilidad completa del juego.

## Reproducción aislada

`setup.ps1` aplicó los 16 parches a la base fijada
`731ad5bfd6e6f265508d0efcca0ba42f9dcf5881` en
`build/integration-clean/pokeemerald`. Árbol resultante idéntico al de trabajo:
`e990d9cea5ae60d66b293bff35b6c5f2725b5a49`.

Se compiló en ese checkout con MINGW32:

```sh
make -C build/integration-clean/port -j4 exe test
```

Los 308 C seleccionados, 15 tablas de datos y 530 canciones se compilaron
a objetos locales; el enlace y las 13 suites terminaron correctamente.
Se reutilizaron el preproc y recursos generados del build GBA existente:
build/assets, gráficos/sonidos convertidos, canciones y headers generados.
No se regeneraron todos esos recursos desde cero. Los fuentes parcheados
y objetos host sí provienen del checkout aislado, sin reutilizar objetos
host del proyecto original. Log: `build/integration-clean-build.log`.

Otras evidencias locales: `build/normal-separation-build.log`,
`build/normal-game-regression/gdb.log`, `build/wild-battle-regression/gdb.log`
y `build/integration-gba-compare.log` (`pokeemerald.gba: OK`).
Se revisaron los nombres de archivos salientes y no se encontraron ROMs,
saves, assets, binarios ni fuentes de pokeemerald fuera de los parches.
El plan antiguo no rastreado del usuario permanece sin cambios.

## Integración local

`main` avanzó mediante `git merge --ff-only codex/milestone-21-integration`
a `b884358`: incluye la cadena de hitos 7–20 y el arreglo de separación
`37b066e`. No hubo conflictos ni push. El registro posterior de este
resultado también se integra mediante fast-forward. La comprobación de
archivos rastreados admite únicamente port/, patches/, AGENTS.md,
README.md, setup.ps1 y .gitignore, sin extensiones de recursos o binarios.
