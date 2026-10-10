import type { Metadata } from "next";
import Link from "next/link";
import { RegistrationForm } from "./registration-form";

export const metadata: Metadata = { title: "Crear cuenta — MascoMatch" };

export default function CreateAccountPage() {
  return <main id="main-content" className="page account-page">
    <Link href="/" className="back-link"><span aria-hidden="true">←</span> Volver al inicio</Link>
    <h1>Creá tu cuenta</h1>
    <p className="page-intro">Gestioná tus avisos y recibí las notificaciones de posibles avistamientos.</p>
    <RegistrationForm />
  </main>;
}
