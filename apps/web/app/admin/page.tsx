import type {Metadata} from "next";
import {Administration} from "./administration";
import "./dashboard.css";
export const metadata:Metadata={title:"Administración — MascoMatch",robots:{index:false,follow:false}};
export default function Page(){return <main id="main-content" className="page admin-page"><h1>Administración</h1><p className="page-intro">Revisá las recomendaciones, las respuestas de los dueños y la actividad de MascoMatch.</p><Administration/></main>;}
