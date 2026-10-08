import type {Metadata} from "next";
import {Administration} from "./administration";
export const metadata:Metadata={title:"Administración — MascoMatch"};
export default function Page(){return <main id="main-content" className="page report-page"><h1>Administración</h1><Administration/></main>;}
