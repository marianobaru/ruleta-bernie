# La Ruleta de Bernie

Draft de fútbol para 2 jugadores en el mismo dispositivo.

1. Cada jugador escribe su nombre y elige la formación (4-3-3, 4-4-2, 3-5-2, 4-2-3-1, 3-4-3 o 5-3-2).
2. En cada ronda tira primero un jugador: sale un club o una selección y elige un futbolista de ese plantel. Con eso define el puesto de la ronda (arquero, defensor, mediocampista o delantero).
3. Después tira el otro jugador: del equipo que le salga tiene que elegir ese mismo puesto.
4. En la ronda siguiente arranca el otro. Cuando las dos canchas tienen sus 11, se revelan los puntajes y gana el que más suma.

Reglas finas:

- El que arranca solo puede elegir puestos que todavía les falten a los dos. Si las formaciones son distintas y ya no queda ningún puesto en común, cada uno elige libremente lo que le falte.
- Si en el equipo que salió no queda ningún futbolista libre para el puesto, ese jugador vuelve a tirar sin perder el turno.
- Un futbolista que ya fichó alguien no se puede volver a elegir, aunque aparezca en otro equipo (por ejemplo, en su club y en su selección).

## Archivos

| Archivo | Qué es |
| --- | --- |
| `index.html` | El juego. |
| `planteles.js` | Planteles y puntajes que usa el juego. Se genera; no editarlo a mano. |
| `datos/wikipedia/*.json` | Planteles bajados de Wikipedia (sección "Current squad"). |
| `datos/puntajes.json` | Puntaje de cada futbolista (estimado, de 1 a 99). Se puede corregir a mano. |
| `herramientas/` | Scripts para bajar planteles y armar `planteles.js`. |

## Actualizar planteles

```bash
python3 -I herramientas/bajar_planteles.py
```

```bash
python3 -I herramientas/armar_planteles.py
```

El segundo script avisa qué futbolistas no tienen puntaje. Esos usan un puntaje base del equipo hasta que se agreguen en `datos/puntajes.json`.

Para probar una partida rápida, abrí el juego con `#rapido` al final de la dirección: la ruleta gira en medio segundo.
