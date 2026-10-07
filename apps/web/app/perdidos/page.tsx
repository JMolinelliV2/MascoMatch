import Link from "next/link";
import type { Metadata } from "next";
import { LostDogs } from "./lost-dogs";

export const metadata: Metadata = { title: "Animales perdidos — PetMatch" };

export default function LostDogsPage() {
  return <main id="main-content" className="page lost-dogs-page">
    <Link href="/" className="back-link"><span aria-hidden="true">←</span> Volver al inicio</Link>
    <div className="lost-dogs-heading">
      <div><h1>Animales perdidos</h1><p className="page-intro">Mirá los avisos y ayudá a que vuelvan a casa.</p></div>
      <Link href="/perdi" className="button button-secondary">Publicar un aviso</Link>
    </div>
    <LostDogs />
  </main>;
}
