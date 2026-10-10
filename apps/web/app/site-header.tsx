"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { NotificationsLink } from "./notifications-link";
import { Icon } from "./ui/pictogram";

const primary = [["/", "Inicio"], ["/perdi", "Perdí una mascota"], ["/avistamiento", "Vi una mascota"], ["/mis-avisos", "Mis avisos"]] as const;
const explore = [["/perdidos", "Animales perdidos"], ["/mapa", "Mapa"], ["/encontre", "Encontré una mascota"], ["/#como-funciona", "Cómo funciona"]] as const;

export function SiteHeader() {
  const pathname = usePathname();
  const [signedIn, setSignedIn] = useState(false);
  useEffect(() => {
    let disposed = false;
    let controller: AbortController | undefined;
    async function load() {
      controller?.abort(); controller = new AbortController();
      const signal = controller.signal;
      try { const response = await fetch("/api/session", { cache: "no-store", signal }); if (response.ok) { const session = await response.json(); if (!disposed && !signal.aborted) setSignedIn(Boolean(session.user)); } } catch { /* Navigation stays available while the session service is unavailable. */ }
    }
    void load(); window.addEventListener("mascomatch:session", load); window.addEventListener("focus", load);
    return () => { disposed = true; controller?.abort(); window.removeEventListener("mascomatch:session", load); window.removeEventListener("focus", load); };
  }, []);
  const visiblePrimary = primary.filter(([href]) => href !== "/mis-avisos" || signedIn);
  const active = (href: string) => href !== "/#como-funciona" && (href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(href + "/"));
  const links = (items: readonly (readonly [string, string])[]) => items.map(([href, label]) => <Link key={href} href={href} aria-current={active(href) ? "page" : undefined}>{label}</Link>);
  return (
    <header className="site-header">
      <a className="skip-link" href="#main-content">Ir al contenido</a>
      <div className="site-header-inner">
        <Link href="/" className="site-name" aria-label="MascoMatch, inicio"><span className="brand-mark"><Icon name="paw" /></span><span>Masco<span className="brand-accent">Match</span></span></Link>
        <nav className="desktop-navigation" aria-label="Navegación principal">
          {links(visiblePrimary)}
          <details className="explore-menu"><summary aria-label="Explorar MascoMatch">Explorar <span aria-hidden="true">⌄</span></summary><div className="explore-links" onClick={event => { if ((event.target as Element).closest("a")) event.currentTarget.closest("details")?.removeAttribute("open"); }}>{links(explore)}</div></details>
        </nav>
        <div className="header-tools">{signedIn && <NotificationsLink />}{!signedIn && <Link href="/crear-cuenta" className="text-button registration-link" aria-current={active("/crear-cuenta") ? "page" : undefined}>Crear cuenta</Link>}<Link href={signedIn ? "/mis-avisos" : "/login"} aria-label={signedIn ? "Ir a mi cuenta" : "Ingresar a mi cuenta"} aria-current={active(signedIn ? "/mis-avisos" : "/login") ? "page" : undefined} className="button button-secondary account-link"><Icon name="user" /><span>{signedIn ? "Mi cuenta" : "Ingresar"}</span></Link></div>
        <details className="mobile-menu"><summary><Icon name="menu" />Menú</summary><nav aria-label="Navegación móvil" onClick={event => { if ((event.target as Element).closest("a")) event.currentTarget.closest("details")?.removeAttribute("open"); }}>{links(visiblePrimary)}{links(explore)}{!signedIn && <Link href="/crear-cuenta" aria-current={active("/crear-cuenta") ? "page" : undefined}>Crear cuenta</Link>}</nav></details>
      </div>
    </header>
  );
}
