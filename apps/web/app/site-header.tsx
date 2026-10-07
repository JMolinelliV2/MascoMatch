import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="site-header">
      <a className="skip-link" href="#main-content">Ir al contenido</a>
      <div className="site-header-inner">
        <Link href="/" className="site-name">PetMatch</Link>
        <nav aria-label="Navegación principal">
          <Link href="/">Inicio</Link>
          <Link href="/perdidos">Animales perdidos</Link>
          <Link href="/#como-funciona">Cómo funciona</Link>
        </nav>
      </div>
    </header>
  );
}
