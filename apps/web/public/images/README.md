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

El primer paso conserva la ilustración de publicación que ya tenía. Los otros tres usan adaptaciones de las referencias aportadas por el usuario el 11 de octubre de 2026.

| Paso | Archivo publicado | Referencia | Escena |
| --- | --- | --- | --- |
| 1 | [how-notice-manypixels.svg](./how-notice-manypixels.svg) | ManyPixels, Content Creation | Publicar un aviso |
| 2 | [how-sighting-reference.webp](./how-sighting-reference.webp) | clue.avif | Mano con lupa y preguntas |
| 3 | [how-review-reference.webp](./how-review-reference.webp) | ia busqueda.avif | Robot analizando información |
| 4 | [how-reunion-reference.webp](./how-reunion-reference.webp) | reunion.jpg | Persona con su perro en el reencuentro |

## Origen y tratamiento

El primer archivo procede de la [galería oficial de ManyPixels](https://www.manypixels.co/gallery), colección Playstroke, identificador `content-creation-33`. Su licencia permite el uso y modificación en sitios personales y comerciales sin atribución visible obligatoria. Se preserva la adaptación coral y azul oscuro ya utilizada.

Las imágenes de los pasos 2, 3 y 4 se adaptaron con la herramienta integrada **imagegen**, a partir de los archivos aportados por el usuario. Se mantuvieron los motivos visuales de las referencias y se ajustaron a coral, azul oscuro, azul y fondos suaves de MascoMatch. La escena del reencuentro muestra al perro sentado junto a la persona que lo acaricia. No se usó la CLI ni una API key del proyecto.

Los archivos finales se convirtieron a WebP con calidad 88, preservando su transparencia y composición:

| Archivo | Dimensiones | Tamaño |
| --- | --- | --- |
| how-sighting-reference.webp | 1536 × 1024 | 89270 bytes |
| how-review-reference.webp | 1685 × 933 | 110220 bytes |
| how-reunion-reference.webp | 1222 × 1287 | 86744 bytes |

Se sirven desde el propio proyecto. Los PNG finales originales se conservan en el directorio de imágenes generadas de Codex. Las referencias del usuario permanecen en su ubicación original. Las escenas son explicativas; no representan un reporte o reencuentro real.

## Prompts finales de adaptación

### Bloque compartido de los pasos 2 y 3

El prompt completo de cada uno de esos pasos es el bloque compartido seguido de `Specific adaptation: ` y la indicación de su escena. Se pasó únicamente su imagen de referencia y se solicitó fondo transparente.

```text
Use case: palette adaptation of a supplied website illustration.
Task: edit the supplied reference illustration for MascoMatch. Preserve its subject, composition, gesture and simple flat vector-like illustration style. This is a faithful palette adaptation, not a new unrelated scene. Keep clean shapes, natural human skin colors and animal fur colors. No 3D, photorealism, shading effects, extra characters, extra limbs, text, logos, numbers or watermark. Brand palette: dark navy #0b2a4a, coral #d93646 (light coral #f26a76 for large fills), blue #0863b4 (light blue #55b8df), soft blue #eff8ff, green #087f5b (soft green #ecfdf5), warm cream #fcfbf8. Replace off-brand purple, lime and turquoise accents with this palette. Remove the plain outer white background to actual transparency so the illustration integrates into the cream website. Retain an organic pale backdrop where present in the reference. Leave generous transparent margins, keep all objects inside the canvas. Crisp flat graphics suitable for a 360px website illustration.
```

### Paso 2: clue.avif

```text
Specific adaptation: Preserve the landscape composition: a human hand emerging from the lower left holding a large magnifying glass, a prominent question mark inside the glass, a few additional question marks around it, and simple foliage at the bottom right. The magnifier is dark navy, the main question mark coral, the sleeve blue, foliage muted brand green and the organic backdrop soft pale blue. Preserve natural peach skin. Maintain the reference's clean, friendly hand-drawn flat appearance. Keep the magnifying glass perfectly circular, with correct hand anatomy. No animal, person body or robot.
```

### Paso 3: ia busqueda.avif

```text
Specific adaptation: Preserve the landscape composition: a friendly rounded robot holding an open laptop, surrounded by three simple floating browser windows showing a chart, a science/analysis symbol and a globe. Keep the rounded robot face with two simple eyes and dark navy outlines. Robot body in brand blue and light blue, laptop in dark navy, small buttons and joints coral, browser headers pale blue with coral dots. Remove purple and orange accent colors. Keep the chart and globe as simple drawings with no text, percentages or labels. No people, dog, cat, brain or extra floating windows.
```

### Paso 4: reunion.jpg

```text
Edit the supplied flat illustration for a family-friendly lost-pet website.
Keep the simple flat vector illustration style and the reunion theme: one fully clothed adult woman kneeling beside her seated brown pet dog. She gently pets the top of the dog's head with one hand and holds its collar area with the other. Dog stays naturally seated beside her with all paws down. Their faces do not touch. Friendly, ordinary everyday pet care, calm and happy.
Retain the reference's overall portrait composition, woman on the right and dog on the left, navy hair in a bun, navy trousers, natural skin and brown dog fur. Change the woman's lime sweater to warm coral #d93646 / #f26a76. Use dark navy #0b2a4a for her hair and trousers. Change turquoise background shapes to very pale brand green #ecfdf5 and soft blue #eff8ff.
Remove the plain white outer background to genuine transparency while keeping the pale organic decorative shapes. Crisp clean flat colored shapes, no texture or 3D, no extra characters, hearts, text, logos, numbers or watermark. Keep all limbs and the entire scene inside the canvas with generous margins.
```
