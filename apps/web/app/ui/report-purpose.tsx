import Link from "next/link";
import { Icon } from "./pictogram";

export function ReportPurpose({ kind }: { kind: "sighting" | "found" }) {
  const found = kind === "found";
  return <aside className={`report-purpose ${found ? "report-purpose-found" : "report-purpose-sighting"}`} aria-label="Cuándo usar este formulario">
    <span className="report-purpose-icon"><Icon name={found ? "heart" : "eye"} /></span>
    <div><h2>{found ? "Si el animal está bajo tu cuidado" : "Si viste un animal que parece perdido"}</h2>
      <p>{found ? "Usá este formulario si está con vos o lo resguardaste en un lugar seguro. Sus datos y fotos ayudarán a que su familia lo reconozca y pueda contactarte." : "Usá este formulario si lo viste y no está bajo tu cuidado. El lugar, la fecha y las fotos que tengas pueden ayudar a su familia a encontrarlo."}</p>
      <Link className="text-button" href={found ? "/avistamiento" : "/encontre"}>{found ? "¿Solo lo viste? Reportá un avistamiento." : "¿Está con vos? Reportá un animal encontrado."}</Link>
    </div>
  </aside>;
}
