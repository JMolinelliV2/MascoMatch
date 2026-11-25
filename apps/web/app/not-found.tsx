import Link from "next/link";
import { ErrorState } from "./ui/error-state";

export default function NotFound() {
  return <main id="main-content" className="page">
    <ErrorState headingLevel={1} title="No encontramos esta página" description="El enlace puede haber cambiado o ya no estar disponible. Podés seguir buscando en los avisos publicados.">
      <Link href="/perdidos" className="button button-primary">Ver mascotas reportadas</Link>
    </ErrorState>
  </main>;
}
