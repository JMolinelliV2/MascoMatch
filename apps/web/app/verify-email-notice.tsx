"use client";
import {useState} from "react";
export function VerifyEmailNotice(){
  const [busy,setBusy]=useState(false);const [message,setMessage]=useState("");
  async function request(){setBusy(true);try{const response=await fetch("/api/account-access/request-verification",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"});setMessage(response.ok?"Revisá tu correo y abrí el enlace de confirmación. Si no aparece, revisá Spam.":"No pudimos enviar el enlace. Intentá de nuevo.");}catch{setMessage("No pudimos enviar el enlace. Intentá de nuevo.");}finally{setBusy(false);}}
  return <aside className="notice"><p>Confirmá tu correo para recibir las alertas de avistamientos.</p><button className="text-button" type="button" disabled={busy} onClick={()=>void request()}>{busy?"Enviando…":"Enviar enlace de confirmación"}</button>{message&&<p role="status">{message}</p>}</aside>;
}
