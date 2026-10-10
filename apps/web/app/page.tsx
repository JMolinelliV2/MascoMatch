import Image from "next/image";
import Link from "next/link";
import { Icon } from "./ui/pictogram";
import { HomeLostAnimals } from "./home-lost-animals";

const steps = [
  { title: "Publicá una mascota perdida", description: "Contanos cómo es, dónde y cuándo la viste por última vez. Podés agregar una foto y los rasgos que ayuden a reconocerla.", detail: "Creá una cuenta y confirmá tu correo para publicar y gestionar tu aviso.", icon: "paw" as const, tone: "feature-icon-0" },
  { title: "Sumá una pista desde la comunidad", description: "Explorá los animales perdidos o el mapa. Si reconocés alguno, abrí su aviso para indicar dónde lo viste, cuándo y adjuntar fotos si tenés.", detail: "Desde una ficha, el avistamiento breve se envía sin cuenta. Para un animal que todavía no esté publicado, usá “Vi una mascota” con tu cuenta.", icon: "pin" as const, tone: "feature-icon-1" },
  { title: "Recibí posibles coincidencias", description: "Comparamos fotos, características, lugar y fecha de los reportes con las búsquedas activas. Las alertas se muestran en tu cuenta y también pueden llegar por correo.", detail: "Cada coincidencia necesita revisión: mirá las fotos, el mapa y los detalles antes de confirmar.", icon: "spark" as const, tone: "feature-icon-2" },
  { title: "Confirmá las pistas y el reencuentro", description: "Si un avistamiento corresponde a tu mascota, confirmalo para registrar esa pista. La búsqueda sigue activa mientras todavía no esté con vos.", detail: "Cuando la recuperes, marcá “Ya la recuperé” o actualizá el estado desde Mis avisos.", icon: "check" as const, tone: "feature-icon-2" },
];

export default function Home() {
  return (
    <main id="main-content" className="home-page">
      <section className="home-hero" aria-labelledby="home-title">
        <div className="hero-content">
          <p className="eyebrow">Más miradas. Más oportunidades.</p>
          <h1 id="home-title">Cada avistamiento<br /><span className="title-accent">puede ayudar a volver a casa.</span></h1>
          <p className="hero-description">Compartí fotos, reportá lo que viste y revisá posibles coincidencias. Tu información puede ayudar a reunir a una mascota con su familia.</p>
          <div className="hero-actions" aria-label="Crear un reporte">
            <Link href="/perdi" className="button button-primary hero-primary"><Icon name="paw" />Perdí una mascota <Icon name="chevron" /></Link>
            <Link href="/avistamiento" className="button button-secondary"><Icon name="eye" />Vi una mascota</Link>
          </div>
          <Link href="/encontre" className="text-button hero-found"><Icon name="heart" />¿Está con vos? Reportá un animal encontrado <Icon name="arrow" /></Link>
          <p className="hero-note"><Icon name="shield" />Perros, gatos y otros animales. Fotos opcionales.</p>
        </div>
        <div className="hero-photo">
          <Image src="/images/dog-hero.jpg" alt="Un perro golden retriever mirando a la cámara" fill priority sizes="(max-width: 760px) 100vw, 50vw" />
        </div>
      </section>

      <section id="como-funciona" className="how-it-works" aria-labelledby="how-title">
        <div className="how-heading">
          <p className="eyebrow">Cada pista puede ayudar</p>
          <h2 id="how-title">Cómo funciona MascoMatch</h2>
          <p className="how-intro">Un aviso empieza la búsqueda. Los avistamientos de la comunidad suman información para que cada familia pueda revisar las pistas y acercarse a un reencuentro.</p>
        </div>
        <ol className="how-steps">
          {steps.map((step, index) => (
            <li key={step.title}>
              <div className="how-step-top"><span className={`feature-icon ${step.tone}`}><Icon name={step.icon} /></span><span className="how-step-number">Paso {index + 1}</span></div>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
              <p className="how-step-detail">{step.detail}</p>
            </li>
          ))}
        </ol>
        <div className="how-help">
          <div>
            <h3>Los detalles hacen la diferencia</h3>
            <p>Una foto clara, una ubicación ajustada en el mapa y una fecha aproximada ayudan a revisar los reportes. Si el animal está a salvo con vos, usá “Encontré una mascota”.</p>
            <Link href="/encontre" className="text-button">Reportar un animal encontrado <Icon name="arrow" /></Link>
          </div>
          <Link href="/perdidos" className="button button-secondary">Ver animales perdidos <Icon name="arrow" /></Link>
        </div>
      </section>
      <HomeLostAnimals />
      <section className="home-support" aria-labelledby="home-support-title"><span className="feature-icon"><Icon name="heart" /></span><div><p className="eyebrow">Apoyo voluntario</p><h2 id="home-support-title">Ayudá a sostener MascoMatch</h2><p>Conocé los niveles de patrocinio y cómo los aportes pueden acompañar las búsquedas de la comunidad.</p></div><Link href="/apoyanos" className="button button-secondary">Conocé cómo apoyar <Icon name="arrow" /></Link></section>
      <footer className="home-footer">
        <span>MascoMatch · Información que ayuda a volver a casa.</span>
        <a href="https://unsplash.com/photos/golden-retriever-x5oPmHmY3kQ" target="_blank" rel="noopener noreferrer">Foto: Victor G / Unsplash</a>
      </footer>
    </main>
  );
}

