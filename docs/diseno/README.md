# Diseño del front

Prototipo navegable hecho con Claude Design (artifact de tipo Design):
**https://claude.ai/artifact/Q5SzerUABzML1Zj8AnQHcT**

Es un diseño, no la app: los botones "Recalcular", "Calcular" y "Aplicar" no llaman a la API. El front real (HTML/JS) se construye a partir de estas pantallas y consume `api/main.py`.

## Pantallas

| Pantalla | Archivo | Qué muestra | Endpoint que la alimenta |
|---|---|---|---|
| Entrar (demo) | `fuentes/Login.dc.html` | Elegir cadena (Cadena Andina / Grupo Pampa, ficticias), sin contraseña | `GET /cadenas` |
| Panel general | `fuentes/Main.dc.html` | Mapa de Argentina por región, una cifra destacada y curva real / puente / pronóstico (nov 2026 – oct 2027) / tendencia | `GET /historico`, `POST /proyeccion` |
| Mi negocio | `fuentes/MiNegocio.dc.html` | Pantalla de la cadena: calendario de demanda de la región, publicaciones de habitaciones con precio actual y recomendado, resumen subir/bajar/mantener e impacto en ingresos | `GET /cadenas/{id}`, `POST /precios` |
| Supuestos económicos | `fuentes/Supuestos.dc.html` | Escenarios Optimista / Base / Pesimista y controles para armar uno propio (aplica al total país) | `POST /proyeccion` |
| Perfil del turista | `fuentes/Perfil.dc.html` | Probabilidad de alojarse en hotel según el perfil del viaje | `POST /hotel` |
| Componente mapa | `fuentes/MapaArgentina.dc.html` | Mapa por las 7 regiones de la EOH, reutilizado en Panel y Mi negocio | `GET /regiones` |

`fuentes/` es una copia de los archivos del artifact (versión del 25-10-2026). Solo se ven dentro de Claude Design: para mirar el diseño usar el link de arriba.

## Decisiones de diseño

- **Visual primero, pocos números:** 2 o 3 cifras grandes por pantalla y el detalle al pasar el mouse o al expandir.
- **Una sola paleta** en todas las pantallas: violeta `#6D28D9` y ámbar `#F59E0B`. Los datos van en una escala azul (mapa y calendario) y en azul/naranja (sube/baja, escenarios). Tiene modo oscuro.
- **7 regiones de la EOH** (INDEC, Metodología N.º 34): La Rioja va en Cuyo y La Pampa en Patagonia. Es la misma tabla que `src/regiones.py`.
- **Ventana de pronóstico:** los 12 meses desde hoy (nov 2026 – oct 2027). Los meses entre el último dato real y hoy se muestran como "puente estimado".
- **Escenarios económicos:** solo cambian el total país. El modelo regional (basado en el trabajo de Tina) no usa variables macro.
- **Precio recomendado:** precio actual × (1 + sensibilidad × desvío de demanda), con el ajuste acotado a ±tope (por defecto 0,5 y 25 %). La regla está en `src/precios.py`.
- **Mapa:** límites provinciales del IGN, simplificados y embebidos en el archivo, así que funciona sin internet.
