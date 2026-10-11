import type { Metadata } from "next";
import Link from "next/link";
import { Icon } from "../ui/pictogram";

export const metadata: Metadata = {
  title: "Términos y condiciones — MascoMatch",
  description: "Condiciones de uso de MascoMatch: publicaciones, avistamientos, posibles coincidencias, cuentas y aportes voluntarios.",
};

const sections = [
  {
    id: "servicio",
    title: "1. Qué ofrece MascoMatch",
    content: <>
      <p>MascoMatch es una plataforma de colaboración para publicar mascotas perdidas, reportar avistamientos y animales encontrados, y revisar posibles coincidencias. El nombre MascoMatch identifica este proyecto; su canal de contacto es <a href="mailto:info@mascomatch.com">info@mascomatch.com</a>.</p>
      <p>La información proviene de las personas que participan. La plataforma ayuda a organizar las pistas, pero no garantiza que un reporte sea correcto, que dos animales sean el mismo ni que se produzca un reencuentro. No sustituye la asistencia veterinaria, los servicios de rescate ni la actuación de las autoridades.</p>
    </>,
  },
  {
    id: "cuentas",
    title: "2. Cuentas y acceso",
    content: <>
      <p>Para publicar desde una cuenta, tenés que proporcionar datos de contacto válidos y confirmar tu correo electrónico. Podés usar un nombre o apodo. Los avistamientos breves enviados desde la ficha de un animal perdido pueden reportarse sin crear una cuenta.</p>
      <p>Cuidá tu contraseña y no compartas el acceso a tu cuenta. Si detectás un acceso que no reconocés, cambiá la contraseña o utilizá la recuperación de cuenta. No suplantes a otras personas ni uses datos de contacto ajenos sin autorización.</p>
    </>,
  },
  {
    id: "publicaciones",
    title: "3. Publicaciones y uso responsable",
    content: <>
      <p>Publicá información que conozcas y diferenciá los hechos de las suposiciones. Revisá la especie, la descripción, el lugar y la fecha antes de enviar. Las fotos son opcionales; si las tenés, pueden ayudar a reconocer al animal.</p>
      <p>Mantené tus avisos actualizados. Si recuperaste a tu mascota, indicá que ya está con vos. Confirmar que un avistamiento corresponde a tu animal registra una pista: la búsqueda sigue activa hasta que marques el reencuentro o cierres el aviso.</p>
      <ul>
        <li>No envíes reportes falsos, duplicados deliberados, spam ni publicidad ajena a la búsqueda.</li>
        <li>No uses la plataforma para vender animales, cometer fraudes, acosar o publicar acusaciones contra personas.</li>
        <li>No publiques documentos, domicilios particulares ni datos personales de otras personas sin una autorización adecuada.</li>
        <li>No intentes acceder a cuentas ajenas, extraer información privada ni interferir con el funcionamiento del servicio.</li>
      </ul>
    </>,
  },
  {
    id: "contenido",
    title: "4. Fotos, textos y reseñas",
    content: <>
      <p>Subí contenido propio o que tengas permiso para utilizar. Conservás los derechos que te correspondan sobre tus fotos y textos. Al publicarlos, autorizás a MascoMatch de forma no exclusiva a almacenarlos, adaptarlos técnicamente y mostrarlos dentro del servicio para difundir reportes y comparar posibles coincidencias. Esa autorización no transfiere su propiedad.</p>
      <p>Los reportes públicos pueden mostrar la descripción del animal, las fotos, la zona y la fecha. Evitá incluir personas identificables o información sensible en las imágenes y los textos. Eliminar metadatos de una foto no elimina los datos visibles dentro de ella.</p>
      <p>Las reseñas son voluntarias y deben reflejar una experiencia real. Podés elegir un apodo o una publicación anónima y retirar tu reseña desde Mis avisos. El cierre de una búsqueda no implica necesariamente que haya ocurrido un reencuentro.</p>
    </>,
  },
  {
    id: "coincidencias",
    title: "5. Coincidencias e inteligencia artificial",
    content: <>
      <p>MascoMatch puede comparar fotos, características, fechas y ubicaciones para proponer posibles coincidencias. Los resultados automáticos pueden contener errores y siempre necesitan revisión humana. Una puntuación de similitud no es una prueba de identidad ni una probabilidad garantizada de que sea tu mascota.</p>
      <p>Un avistamiento enviado desde un aviso se presenta al dueño como una pista vinculada a ese caso. Su recepción y el resultado de la comparación son cosas diferentes: puede estar pendiente de análisis o resultar incompatible. Vincular un reporte, recibir una alerta o confirmar una pista no acredita por sí solo la propiedad del animal.</p>
    </>,
  },
  {
    id: "ubicacion",
    title: "6. Ubicación y cuidado al contactar",
    content: <>
      <p>Los mapas públicos muestran ubicaciones aproximadas. La ubicación más precisa de un avistamiento puede compartirse de forma privada con el dueño en las alertas de su caso. Las direcciones sugeridas y la ubicación del dispositivo pueden ser inexactas; revisá el lugar y ajustá el pin cuando corresponda.</p>
      <p>Los datos de contacto guardados en tu cuenta no se muestran automáticamente en las fichas públicas. Si decidís compartir tu correo de un reporte, se facilita de forma privada a los dueños que reciban la posible coincidencia. Si escribís un correo, un teléfono o una dirección dentro de una descripción pública, esa información puede quedar visible.</p>
      <p>Antes de coordinar un encuentro, verificá la información y cuidá tu seguridad. No envíes dinero, contraseñas, códigos de acceso ni documentos a alguien que dice haber encontrado un animal. Ante una situación de peligro o un animal que necesita atención urgente, buscá asistencia apropiada.</p>
    </>,
  },
  {
    id: "notificaciones",
    title: "7. Notificaciones y correo electrónico",
    content: <>
      <p>Las alertas se consultan dentro de la cuenta y también pueden enviarse por correo. Podés activar o desactivar los correos de alertas y recordatorios desde Mi cuenta. Los mensajes que solicitás para confirmar el correo, cambiarlo o recuperar la contraseña mantienen su finalidad de acceso y seguridad.</p>
      <p>Los envíos y los análisis pueden demorarse o fallar. La aceptación de un correo por el servicio de envío no garantiza su llegada inmediata ni que quede en la bandeja de entrada. Para revisar el estado de una pista, consultá también tus avisos y notificaciones.</p>
    </>,
  },
  {
    id: "datos",
    title: "8. Datos personales y consultas",
    content: <>
      <p>El servicio utiliza los datos necesarios para gestionar cuentas, publicar reportes, almacenar fotos, comparar pistas, enviar comunicaciones y atender consultas. La información pública y los datos privados de cuenta y contacto tienen finalidades diferentes; compartir un reporte no autoriza otros usos de los datos personales.</p>
      <p>Podés actualizar tu contacto y tus preferencias desde Mi cuenta. Para solicitar acceso, rectificación o supresión de datos personales, o consultar cómo se utilizan, escribí a <a href="mailto:info@mascomatch.com">info@mascomatch.com</a> o usá el <Link href="/contacto">formulario de contacto</Link>. Podemos pedir la información mínima necesaria para comprobar que la solicitud corresponde a tus datos.</p>
      <p>Estas condiciones de uso no sustituyen la información de privacidad que debe acompañar la recolección y el tratamiento de datos personales.</p>
    </>,
  },
  {
    id: "eliminacion",
    title: "9. Cierre de avisos y eliminación de cuenta",
    content: <>
      <p>Podés gestionar y cerrar tus avisos desde Mis avisos. Cerrar un aviso lo retira de las búsquedas activas; no equivale a eliminar tu cuenta.</p>
      <p>Al eliminar tu cuenta desde Mi cuenta, se eliminan tus mascotas, avisos de pérdida, reseñas, perfil, sesiones y notificaciones. Los avistamientos y reportes de animales encontrados se conservan como pistas de la comunidad, desvinculados de tu cuenta y sin compartir tu contacto de cuenta. También pueden conservar sus fotos y descripciones.</p>
      <p>Desvincular un reporte no elimina los datos que hayas incluido dentro de su texto o sus fotos. Si necesitás retirar información personal de esos contenidos, contactanos. Las copias de respaldo tienen un ciclo de conservación propio y no desaparecen inmediatamente al borrar un registro.</p>
    </>,
  },
  {
    id: "moderacion",
    title: "10. Denuncias y moderación",
    content: <>
      <p>Podés denunciar un aviso desde su ficha o informar un problema mediante Contacto. Una denuncia inicia una revisión y no confirma que el reporte sea falso.</p>
      <p>Podemos ocultar contenido o restringir cuentas cuando exista un incumplimiento de estas condiciones, una afectación de derechos, fraude, abuso o un riesgo de seguridad. Si necesitás aclarar una decisión de moderación o corregir una publicación, escribinos con la referencia del reporte.</p>
    </>,
  },
  {
    id: "aportes",
    title: "11. Gratuidad y aportes voluntarios",
    content: <>
      <p>Actualmente, publicar avisos, reportar avistamientos y consultar las búsquedas es gratuito. Los niveles de Apoyanos son propuestas de aportes voluntarios en pesos uruguayos. La plataforma todavía no recibe pagos ni genera cobros por elegir un monto o una frecuencia.</p>
      <p>Cuando se habiliten los pagos, se informarán las condiciones de cobro, la frecuencia, las opciones de cancelación y los datos del receptor antes de solicitar un aporte. Apoyar el proyecto no otorga prioridad sobre otras búsquedas ni garantiza resultados.</p>
    </>,
  },
  {
    id: "disponibilidad",
    title: "12. Disponibilidad y alcance de la herramienta",
    content: <>
      <p>La plataforma puede experimentar interrupciones por mantenimiento, problemas técnicos o fallos de servicios de mapas, almacenamiento y correo. La información de la comunidad y las herramientas automáticas pueden estar incompletas o desactualizadas.</p>
      <p>Estas limitaciones describen el alcance del servicio. No implican una renuncia a los derechos que te reconozca la legislación aplicable ni excluyen las responsabilidades que legalmente correspondan a quien opere MascoMatch.</p>
    </>,
  },
  {
    id: "versiones",
    title: "13. Versiones y contacto",
    content: <>
      <p>Esta es una versión preliminar para el piloto. Antes de la puesta en marcha pública se completará la identificación legal del responsable y la información de privacidad. Las futuras versiones indicarán su fecha y los cambios que correspondan; tu silencio no se considerará aceptación de nuevas obligaciones.</p>
      <p>Si tenés dudas sobre estas condiciones, una publicación o tus datos, podés escribir a <a href="mailto:info@mascomatch.com">info@mascomatch.com</a> o comunicarte desde <Link href="/contacto">Contacto y sugerencias</Link>.</p>
    </>,
  },
] as const;

export default function TermsPage() {
  return <main id="main-content" className="page legal-page">
    <Link href="/" className="back-link"><span aria-hidden="true">←</span> Volver al inicio</Link>
    <header className="legal-heading">
      <p className="eyebrow">Uso de la plataforma</p>
      <h1>Términos y condiciones</h1>
      <p className="page-intro">Conocé las condiciones para publicar, compartir pistas y participar en MascoMatch.</p>
      <p className="legal-version">Versión preliminar del piloto · Actualizada el <time dateTime="2026-10-11">11 de octubre de 2026</time></p>
    </header>
    <aside className="legal-summary" aria-labelledby="legal-summary-title">
      <Icon name="shield" />
      <div><h2 id="legal-summary-title">Una comunidad que se cuida</h2><p>Publicar y buscar es gratis. Compartí información real, cuidá los datos de otras personas y revisá las pistas antes de confirmar una coincidencia.</p></div>
    </aside>
    <details className="legal-index">
      <summary>Índice de contenidos <Icon name="chevron" /></summary>
      <nav aria-label="Secciones de los términos y condiciones"><ol>{sections.map(section => <li key={section.id}><a href={`#${section.id}`}>{section.title}</a></li>)}</ol></nav>
    </details>
    <article className="legal-content" aria-label="Condiciones de uso de MascoMatch">
      {sections.map(section => <section key={section.id} id={section.id} aria-labelledby={`${section.id}-title`}><h2 id={`${section.id}-title`}>{section.title}</h2>{section.content}</section>)}
    </article>
  </main>;
}
