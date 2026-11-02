import Image from "next/image";
import Link from "next/link";
import type { ReactNode } from "react";
import { Icon } from "./pictogram";

export function AuthLayout({ mode, children }: { mode: "login" | "register"; children: ReactNode }) {
  return <main id="main-content" className={`page auth-page auth-page--${mode}`}>
    <div className="auth-shell">
      <section className="auth-content" aria-labelledby="auth-title">
        <nav className="auth-switch" aria-label="Acceso a tu cuenta">
          <Link href="/login" aria-current={mode === "login" ? "page" : undefined}>Ingresar</Link>
          <Link href="/crear-cuenta" aria-current={mode === "register" ? "page" : undefined}>Crear cuenta</Link>
        </nav>
        <h1 id="auth-title">{mode === "login" ? "Ingresá a tu cuenta" : "Creá tu cuenta"}</h1>
        {children}
      </section>
      <div className="auth-visual" aria-hidden="true">
        <span className="auth-visual-badge"><Icon name="paw" />Cada pista suma.</span>
        <div className="auth-artwork"><Image src={mode === "login" ? "/images/auth-login-illustration.webp" : "/images/auth-register-illustration.webp"} alt="" fill loading="eager" sizes="(max-width: 760px) 260px, (max-width: 950px) 320px, 520px" className="auth-illustration" /></div>
        <div className="auth-visual-copy"><p>Para que más mascotas<br />vuelvan a casa.</p><span>Una comunidad que acompaña cada búsqueda.</span></div>
      </div>
    </div>
  </main>;
}
