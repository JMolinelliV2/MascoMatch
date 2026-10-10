import type { Metadata } from "next";
import Link from "next/link";
import { AccountSettings } from "./account-settings";

export const metadata: Metadata = { title: "Mi cuenta — MascoMatch" };

export default function AccountPage() {
  return <main id="main-content" className="page account-page">
    <Link href="/mis-avisos" className="back-link"><span aria-hidden="true">←</span> Volver a mis avisos</Link>
    <h1>Mi cuenta</h1>
    <p className="page-intro">Actualizá tu contacto, configurá tus notificaciones y gestioná tu cuenta.</p>
    <AccountSettings />
  </main>;
}
