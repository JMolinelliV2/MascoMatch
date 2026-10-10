import type {Metadata} from "next";
import {MyReports} from "./my-reports";
export const metadata:Metadata={title:"Mis avisos — MascoMatch"};
export default function Page(){return <main id="main-content" className="page report-page my-reports-page"><h1>Mis avisos</h1><p className="page-intro">Revisá tus publicaciones, las coincidencias y el estado de búsqueda.</p><MyReports/></main>;}
