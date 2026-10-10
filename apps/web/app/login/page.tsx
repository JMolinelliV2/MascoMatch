import type { Metadata } from "next";
import Link from "next/link";
import { LoginForm } from "./login-form";

export const metadata: Metadata = { title: "Ingresar — MascoMatch" };

export default function LoginPage() {
  return <main id="main-content" className="page account-page">
    <Link href="/" className="back-link"><span aria-hidden="true">←</span> Volver al inicio</Link>
    <h1>Ingresá a tu cuenta</h1>
    <p className="page-intro">Gestioná tus avisos y revisá las notificaciones de posibles avistamientos.</p>
    <LoginForm />
  </main>;
}
