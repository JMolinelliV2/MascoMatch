# Imagen de portada

`dog-hero-generated.jpg`: imagen ilustrativa original de un golden retriever en un jardín, creada para MascoMatch con la herramienta integrada **imagegen** el 11 de octubre de 2026.

- Resolución: 1536 × 1024 píxeles, proporción 3:2.
- Formato de publicación: JPEG optimizado, calidad 88, aproximadamente 180 KB.
- Tratamiento: conversión del PNG generado a JPEG sin recorte ni cambios de composición.
- Uso: portada; no representa un animal publicado ni un reencuentro real.
- Distribución: archivo local incluido en el proyecto, servido mediante el componente de imágenes de Next.js.

La portada sustituye la fotografía externa anterior. Se retiró su archivo y su crédito del footer. La trazabilidad de la imagen generada queda documentada aquí.

## Prompt de generación

```text
Use case: photorealistic-natural.
Asset type: original hero image for MascoMatch, a community website helping reunite lost pets with their families.
Primary request: create a new, original photorealistic image of a friendly golden retriever sitting in a peaceful garden and looking toward the camera.
Scene/backdrop: softly blurred garden foliage, subtle cream and warm green tones, no identifiable location.
Subject: one healthy adult golden retriever, natural golden fur, realistic eyes and nose, gently relaxed open mouth, no accessories.
Composition/framing: landscape 3:2 image, eye-level medium portrait showing the entire head, ears, neck and upper chest; center the dog with generous breathing room above and beside the head, keeping facial features within the central area so a website crop in desktop and mobile remains comfortable. No text overlay is needed; the website copy appears beside the image.
Lighting/mood: soft natural morning light, welcoming and calm, detailed natural fur, believable proportions, shallow depth of field, natural color balance.
Constraints: original fictional animal for illustration; no real lost-pet report, no people, no additional animals, no text, no logos, no watermarks, no graphic elements, no copyrighted photograph references.
```


# Ilustraciones de Cómo funciona

Cuatro escenas originales creadas para MascoMatch con la herramienta integrada **imagegen** el 11 de octubre de 2026, usando las referencias del usuario como inspiración de composición y tono. Las imágenes son conceptuales; no representan usuarios, reportes o reencuentros reales.

| Archivo publicado | Escena | Tamaño |
| --- | --- | --- |
| [how-notice-generated.webp](./how-notice-generated.webp) | Publicación de un aviso | 222556 bytes |
| [how-sighting-generated.webp](./how-sighting-generated.webp) | Avistamiento de la comunidad | 209440 bytes |
| [how-review-generated.webp](./how-review-generated.webp) | Revisión humana de pistas | 221208 bytes |
| [how-reunion-generated.webp](./how-reunion-generated.webp) | Reencuentro | 179736 bytes |

Resolución de cada archivo: 1254 × 1254 píxeles. El PNG original se convirtió a WebP con calidad 88, preservando el canal alfa, sin recorte ni alteración de la composición. Los originales se conservan en el directorio de imágenes generadas de Codex; los archivos publicados forman parte del repositorio.

## Prompts de las ilustraciones

El prompt completo de cada imagen es el bloque compartido seguido de `Scene: ` y el bloque correspondiente a su escena. Se utilizó el modo integrado de imagegen, con `transparent_background: true`, sin CLI ni API key del proyecto.

### Bloque compartido

```text
Use case: illustration for a website.
Asset type: one original isolated editorial illustration for the MascoMatch lost-pet community website.
Art direction: a warm, playful, sophisticated flat vector-like editorial drawing with slightly hand-drawn dark navy thin outlines, clean large shapes, rounded silhouettes, expressive friendly human faces, believable anatomy. Limited palette: dark navy #0b2a4a, warm coral #ef5965, pale sky blue #d8ebf6, muted teal #78b9a2, touches of soft mustard #f5c569, warm cream. No gradients, no photographic detail, no 3D, no UI mockup. One pale organic rounded blob behind the subjects, a few small drawn stars or dots. Generous transparent outer margins; the blob remains part of the illustration but the rest of the background is transparent.
Composition: centered full vignette, square canvas, subjects and props entirely within the canvas, no cropped hands or feet, mostly front/three-quarter view, detailed enough to read clearly at 300px wide, illustration fills about 80% of canvas. Original fictional humans and animals, no resemblance to a known artist or specific copyrighted character.
Constraints: no words, letters, numerals, watermark, logo, brand mark or border. No buttons or interface text. Avoid crowded details. Preserve transparent background.
```

### how-notice-generated.webp

```text
Scene: A young adult woman with dark wavy hair and a coral cardigan seated on a low stool, using a large smartphone to publish a missing-pet notice. Beside her is a single paper poster displaying only a friendly illustrated golden dog's face and a little paw symbol, no text. A small potted plant, an oversized camera outline and one paperclip add a playful editorial touch. The illustrated dog on the poster is not a real animal present in the scene. Pale sky-blue organic backdrop. Mood: hopeful and caring.
```

### how-sighting-generated.webp

```text
Scene: A young adult man with short dark hair and a mustard overshirt crouches beside a friendly small golden dog sitting near a simple street tree. He is taking a photo with a smartphone to help identify the dog. A large coral location pin, a simple small map folded on the ground, and two thin directional strokes communicate a community sighting. A pale sky-blue organic backdrop. Healthy relaxed dog, kind respectful body language, hopeful rather than distressed.
```

### how-review-generated.webp

```text
Scene: An adult woman with brown hair in a bun, muted teal sweater and navy trousers calmly examines two large printed photographs of the same friendly golden dog's face, one in her hand and one beside her, while sitting at a small simple desk. A large outline magnifying glass and coral notification bell float nearby as conceptual props. A modest open laptop sits on the desk with a simple paw outline on its screen, no UI text. Pale sky-blue organic backdrop. The human is reviewing clues thoughtfully, not an autonomous robot.
```

### how-reunion-generated.webp

```text
Scene: A young adult woman in a coral sweater and navy trousers kneels and warmly hugs a happy golden dog while a friendly small cream-and-gray cat sits beside them. Their complete bodies remain inside the composition, joyful faces, gentle natural pose, correct anatomy. A simple outline house roof behind them and two small coral hearts communicate a reunion at home. Pale mint organic backdrop. A sweet hopeful intimate scene, no accessories or extra limbs.
```
