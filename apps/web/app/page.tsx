import Image from "next/image";
import Link from "next/link";

const steps = [
  { title: "Describí al animal", description: "Contanos cómo es. Una foto puede ayudar, pero también podés compartir una descripción." },
  { title: "Indicá dónde y cuándo", description: "Buscá una dirección o usá tu ubicación para señalar el lugar del reporte." },
  { title: "Revisá y publicá", description: "Confirmá la información y dejá tu contacto para registrar el reporte." },
];

export default function Home() {
  return (
    <main id="main-content" className="home-page">
      <section className="home-hero" aria-labelledby="home-title">
        <div className="hero-content">
          <p className="eyebrow">Mascotas perdidas y encontradas</p>
          <h1 id="home-title">Ayudemos a que<br />vuelvan a casa.</h1>
          <p className="hero-description">Si perdiste a tu mascota o viste un animal que podría estar perdido, compartí la información acá.</p>
          <div className="hero-actions" aria-label="Crear un reporte">
            <Link href="/perdi" className="button button-primary hero-primary">Perdí una mascota <span aria-hidden="true">→</span></Link>
            <Link href="/avistamiento" className="button button-secondary">Vi una mascota</Link>
            <Link href="/encontre" className="button button-secondary">Encontré una mascota</Link>
          </div>
          <p className="hero-note">Perros, gatos y otros animales. Podés ayudar incluso si no tenés una foto.</p>
        </div>
        <div className="hero-photo">
          <Image src="/images/dog-hero.jpg" alt="Un perro golden retriever mirando a la cámara" fill priority sizes="(max-width: 760px) 100vw, 50vw" />
        </div>
      </section>

      <section className="lost-dogs-invitation" aria-labelledby="lost-dogs-home-title">
        <div><h2 id="lost-dogs-home-title">¿Reconocés a alguno?</h2><p>Mirá los perros publicados como perdidos.</p></div>
        <Link href="/perdidos" className="button button-secondary">Ver perros perdidos <span aria-hidden="true"> →</span></Link>
      </section>
      <section id="como-funciona" className="how-it-works" aria-labelledby="how-title">
        <h2 id="how-title">Cada dato puede ayudar.</h2>
        <p className="section-intro">Publicar un reporte lleva tres pasos.</p>
        <ol className="how-steps">
          {steps.map((step, index) => (
            <li key={step.title}>
              <span className="how-number" aria-hidden="true">{index + 1}</span>
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </li>
          ))}
        </ol>
      </section>
      <footer className="home-footer">
        <span>PetMatch · Información que ayuda a volver a casa.</span>
        <a href="https://unsplash.com/photos/golden-retriever-x5oPmHmY3kQ" target="_blank" rel="noopener noreferrer">Foto: Victor G / Unsplash</a>
      </footer>
    </main>
  );
}

