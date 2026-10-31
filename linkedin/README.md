# Serie LinkedIn: agente de triaje de OTs

Seis posts, martes y jueves durante tres semanas. Cada carpeta tiene todo lo que necesita su post:

- `texto.txt`: el texto listo para pegar, sin formato (LinkedIn no admite Markdown).
- `video.mp4` (1080×1350): **súbelo como vídeo**. LinkedIn lo reproduce solo en el feed y se ve más nítido que el GIF.
- `animacion.gif` (720×900): la misma animación, por si prefieres subirla como imagen.
- `imagen.png`: solo en el post 3.

Todos los vídeos salen de una ejecución real del agente con Groq (`openai/gpt-oss-120b`). Los datos son inventados.

| # | Fecha | Carpeta | Archivo que se sube | Extra |
|---|---|---|---|---|
| 1 | Mar 3 nov 2026 | `post-1-el-problema` | `video.mp4` | |
| 2 | Jue 5 nov 2026 | `post-2-que-es-langgraph` | `video.mp4` | |
| 3 | Mar 10 nov 2026 | `post-3-disenar-antes-de-programar` | `imagen.png` | |
| 4 | Jue 12 nov 2026 | `post-4-el-agente-en-accion` | `video.mp4` | Primer comentario: `comentario.txt` + `comentario-traza-langsmith.png` |
| 5 | Mar 17 nov 2026 | `post-5-la-persona-en-el-bucle` | `video.mp4` | |
| 6 | Jue 19 nov 2026 | `post-6-lecciones-y-repo` | `video.mp4` | |

LinkedIn no deja mezclar vídeo e imágenes en el mismo post. Por eso la traza de LangSmith del post 4 va en el primer comentario.

## Antes de empezar

- [ ] Revisar con Seitech si quieres mencionar la empresa (los posts están escritos a título personal).
- [ ] Antes del post 6: hacer público el repo y pasar los cambios de la rama `claude/awesome-dijkstra-d6tks8` a la principal.
- [ ] Revocar las claves de Groq y LangSmith que se pegaron en el chat y crear otras nuevas.

## Con la extensión de Claude para Chrome

Descarga esta carpeta a tu ordenador. La forma más sencilla es bajar el repo de GitHub como ZIP desde la rama `claude/awesome-dijkstra-d6tks8`.

La extensión puede abrir LinkedIn, pegar el texto y dejar la publicación programada. Lo que puede que no consiga es elegir un archivo de tu ordenador en el diálogo de subida. Si se atasca ahí, adjunta tú el vídeo cuando te lo pida y deja que siga.

Pide un post cada vez. Texto para pegar en la extensión (cambia el número, la fecha y la carpeta):

```
Abre linkedin.com y empieza una publicación nueva.
1. Pega exactamente este texto, sin cambiar nada:
<pega aquí el contenido de texto.txt>
2. Avísame para que adjunte el archivo video.mp4 de la carpeta post-1-el-problema.
3. Cuando esté adjunto, usa el reloj de "Programar" para el martes 3 de noviembre de 2026 a las 8:30.
4. Antes de pulsar "Programar", enséñame cómo ha quedado y espera a que te diga que sí.
No publiques nada sin mi confirmación.
```

Para el post 4, cuando ya esté publicado:

```
Abre mi publicación de LinkedIn de hoy sobre el agente de triaje y escribe un comentario con este texto:
<pega aquí el contenido de comentario.txt>
Avísame para que adjunte la imagen comentario-traza-langsmith.png y espera mi confirmación antes de enviarlo.
```

La hora de las 8:30 es una propuesta. Cámbiala si tu red interactúa más en otro momento.
