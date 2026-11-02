import Link from "next/link";
import { Icon } from "./ui/pictogram";

const navigation = [
  {
    id: "footer-explore-title",
    title: "Explorá",
    links: [
      { href: "/perdidos", label: "Mascotas reportadas" },
      { href: "/mapa", label: "Mapa de reportes" },
      { href: "/#como-funciona", label: "Cómo funciona" },
    ],
  },
  {
    id: "footer-help-title",
    title: "Ayudá a encontrar",
    links: [
      { href: "/perdi", label: "Perdí una mascota" },
      { href: "/avistamiento", label: "Vi una mascota" },
      { href: "/encontre", label: "Encontré una mascota" },
    ],
  },
  {
    id: "footer-community-title",
    title: "Cómo apoyarnos",
    links: [
      { href: "/apoyanos", label: "Conocé cómo apoyar" },
      { href: "/contacto", label: "Contacto y sugerencias" },
    ],
  },
  {
    id: "footer-legal-title",
    title: "Legales",
    links: [
      { href: "/terminos", label: "Términos y condiciones" },
      { href: "/privacidad", label: "Privacidad" },
    ],
  },
] as const;

export function SiteFooter() {
  return (
    <footer id="site-footer" className="site-footer">
      <div className="site-footer-inner">
        <div className="footer-content">
          <div className="footer-brand">
            <Link href="/" className="site-name" aria-label="MascoMatch, inicio">
              <span className="brand-mark"><Icon name="paw" /></span>
              <span>Masco<span className="brand-accent">Match</span></span>
            </Link>
            <p className="footer-description">Avisos y avistamientos para que más mascotas vuelvan a casa.</p>
            <p className="footer-free"><Icon name="heart" />Publicar y buscar es gratis.</p>
          </div>
          <div className="footer-navigation-groups">
            {navigation.map(group => (
              <nav key={group.id} className="footer-navigation" aria-labelledby={group.id}>
                <h2 id={group.id}>{group.title}</h2>
                <ul>{group.links.map(link => <li key={link.href}><Link href={link.href}>{link.label}</Link></li>)}</ul>
              </nav>
            ))}
          </div>
        </div>
        <div className="footer-bottom">
          <p>© {new Date().getFullYear()} MascoMatch</p>
        </div>
      </div>
    </footer>
  );
}
