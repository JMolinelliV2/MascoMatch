import Image from "next/image";
import Link from "next/link";
import { Icon } from "./ui/pictogram";
import { HomeLostAnimals } from "./home-lost-animals";

const steps = [
  { title: "Compartí los datos", description: "Describí al animal y subí una foto si tenés. Cada detalle puede ayudar a reconocerlo.", icon: "camera" as const },
  { title: "Reportá un avistamiento", description: "Si viste un animal, indicá el lugar y cuándo fue. También podés ayudar sin una foto.", icon: "pin" as const },
  { title: "Revisá las coincidencias", description: "Comparamos los reportes con avisos activos. El dueño puede revisar las posibles coincidencias.", icon: "spark" as const },
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
        <h2 id="how-title" className="sr-only">Cómo funciona MascoMatch</h2>
        <ol className="how-steps">
          {steps.map((step, index) => (
            <li key={step.title}>
              <span className={`feature-icon ${["feature-icon-0", "feature-icon-1", "feature-icon-2"][index]}`}><Icon name={step.icon} /></span>
              <div><h3>{step.title}</h3><p>{step.description}</p></div>
            </li>
          ))}
        </ol>
      </section>
      <HomeLostAnimals />
      <footer className="home-footer">
        <span>MascoMatch · Información que ayuda a volver a casa.</span>
        <a href="https://unsplash.com/photos/golden-retriever-x5oPmHmY3kQ" target="_blank" rel="noopener noreferrer">Foto: Victor G / Unsplash</a>
      </footer>
    </main>
  );
}

