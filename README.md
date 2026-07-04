# Buscador Universal Venezuela

Buscador web de solo lectura para consultar, desde una sola pantalla, varias
plataformas ciudadanas de personas reportadas tras el terremoto de Venezuela
2026.

La app consulta fuentes externas en vivo, muestra resultados por fuente y enlaza
siempre al sitio original para revisar la ficha o la plataforma pública.

> La información proviene de plataformas ciudadanas y no está verificada.
> Confirma siempre en la fuente original antes de actuar.

## Qué hace

- Busca por nombre, apellido o cédula.
- Consulta 14 fuentes directas desde el backend Flask.
- Lista también fuentes indexadas de forma indirecta por agregadores.
- Muestra enlaces al sitio público de cada fuente.
- Entrega resultados progresivamente con Server-Sent Events.
- No escribe ni modifica datos en ninguna plataforma externa.

## Estado de la fuente con reCAPTCHA

La fuente `desaparecidos_terremoto`
(`<https://desaparecidosterremotovenezuela.com/>`) exige un token reCAPTCHA v3
para acceder a su API.

El formulario permite pegar un token manual, pero actualmente esa integración no
funciona de forma confiable: incluso con el `site key` público y la acción
`submit`, la API externa puede responder `403 Verificación reCAPTCHA fallida`.

Por eso:

- Si no hay token, esa fuente se omite.
- Si el token falla, esa fuente aparece como omitida.
- Parte de esa data puede aparecer indirectamente mediante Hazlo Hoy, que agrega
  varias plataformas.

Snippet usado para intentar generar el token desde la consola del sitio original:

```js
await new Promise((ok) => grecaptcha.ready(ok));
await grecaptcha.execute('6LeBfDUtAAAAAMw1Wtkd58bst6vEnLOi3_NAjGD0',{action:'submit'})
```

## Uso local

Requiere Python 3.10 o superior.

Windows:

```bat
run.bat
```

Linux/macOS:

```bash
./run.sh
```

Manual:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Abre:

```text
http://127.0.0.1:5000
```

## Uso por línea de comandos

```bash
python cli.py "maria fernanda perez"
python cli.py 12345678
python cli.py "jose g" --fuentes tebusco,aquiestoyvenezuela
python cli.py "ana diaz" --json
python cli.py --listar-fuentes
```

## Fuentes directas

| Clave | Plataforma | Sitio |
|---|---|---|
| `venezuelareporta` | Venezuela Reporta | <https://venezuelareporta.org/> |
| `hazlohoy` | Hazlo Hoy | <https://terremoto.hazlohoy.org/> |
| `aquiestoyvenezuela` | Aquí Estoy Venezuela | <https://aquiestoyvenezuela.com/> |
| `localizapacientes` | Localiza Pacientes | <https://localizapacientes.com/> |
| `tebusco` | Te Busco | <https://www.tebusco.app/> |
| `hospitalesenvenezuela` | Hospitales en Venezuela | <https://hospitalesenvenezuela.com/> |
| `desaparecidos_terremoto` | Desaparecidos Terremoto Venezuela | <https://desaparecidosterremotovenezuela.com/> |
| `sosven` | SOS Venezuela | <https://sosven.site/> |
| `desaparecidosvenezuela` | Desaparecidos Venezuela | <https://www.desaparecidosvenezuela.com/> |
| `busquedavzla` | Búsqueda VZLA | <https://busquedavzla.netlify.app/> |
| `ucv_aparecidos` | UCV Aparecidos | <https://ucv-aparecidos.vercel.app/> |
| `localizadosvenezuela` | Localizados Venezuela | <https://localizadosvenezuela.com/> |
| `ubicame` | 911 Ubícame | <https://911.ubica.me/> |
| `encuentralos` | Encuéntralos | <https://encuentralos.tecnosoft.dev/> |

## Fuentes indirectas

Estas no se consultan directamente, pero pueden llegar por agregadores:

| Fuente | Sitio | Vía |
|---|---|---|
| Venezuela Te Busca | <https://venezuelatebusca.com/> | Hazlo Hoy / Yummy SOS |
| Terremoto Venezuela (.com) | <https://terremotovenezuela.com/> | Hazlo Hoy |
| Terremoto Venezuela (app) | <https://terremotovenezuela.app/> | Hazlo Hoy |
| Yummy SOS | <https://sos.yummyrides.com/personas> | Agregador federado |

## Despliegue gratis recomendado: Koyeb

Koyeb permite desplegar una app Flask desde GitHub con HTTPS automático y una
instancia gratuita. La instancia gratuita escala a cero si no recibe tráfico, así
que la primera consulta después de un rato puede tardar más.

Pasos:

1. Crea un repositorio en GitHub y sube este proyecto.
2. Entra a <https://www.koyeb.com/>.
3. Crea un nuevo Web Service.
4. Elige GitHub como fuente y selecciona este repositorio.
5. Elige despliegue con Dockerfile.
6. Usa la instancia gratuita.
7. Publica el servicio.

El `Dockerfile` ya incluido levanta la app con:

```bash
gunicorn --bind 0.0.0.0:${PORT:-7860} --workers 2 --threads 4 --timeout 120 app:app
```

Koyeb asignará una URL pública HTTPS para consultar el buscador remotamente.

## Alternativa gratis: Hugging Face Spaces

También puede desplegarse como Docker Space:

1. Crea un Space en <https://huggingface.co/spaces>.
2. Selecciona SDK `Docker`.
3. Sube estos archivos al repo del Space.
4. El contenedor usará el puerto `7860`, compatible con Spaces.

Esta alternativa funciona, pero Koyeb es más natural para una app Flask pública
general.

## Estructura

```text
app.py                Servidor Flask y endpoints HTTP/SSE
cli.py                Interfaz de línea de comandos
requirements.txt      Dependencias Python
Dockerfile            Despliegue en Koyeb/Hugging Face Spaces
run.bat / run.sh      Arranque local
buscador/             Lógica de fuentes y búsqueda
web/                  HTML, CSS y JS del frontend
```

## Notas técnicas

- El endpoint `/api/fuentes` devuelve el catálogo de fuentes y enlaces.
- El endpoint `/api/buscar` emite eventos SSE con resultados por fuente.
- Las fuentes grandes pueden tardar porque algunas descargan páginas o datasets.
- `max_paginas` limita el recorrido en fuentes paginadas.
- Las claves públicas incluidas son visibles en los frontends originales; no son
  secretos.

## Licencia

Uso humanitario libre, sin garantía.
