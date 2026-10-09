import {Suspense} from "react";
import {AccountAccessForm} from "../account-access-form";
export const metadata={title:"Confirmar correo — MascoMatch"};
export default function Page(){return <main id="main-content" className="page report-page"><h1>Confirmá tu correo</h1><p>Esto permite enviarte alertas de posibles avistamientos.</p><Suspense fallback={<p>Cargando…</p>}><AccountAccessForm purpose="verify"/></Suspense></main>;}
