import type { Metadata } from "next";
import "leaflet/dist/leaflet.css";
import "./globals.css";
import { SiteHeader } from "./site-header";

export const metadata: Metadata = {
  title: "PetMatch — Mascotas perdidas",
  description: "Registrá una mascota perdida, un avistamiento o un animal encontrado.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es-UY" data-scroll-behavior="smooth">
      <body><SiteHeader />{children}</body>
    </html>
  );
}

