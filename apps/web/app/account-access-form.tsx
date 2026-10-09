"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import type { FormEvent } from "react";
export function AccountAccessForm({purpose}:{purpose:"verify"|"recover"}){
  const code=useSearchParams().get("codigo");
  const [busy,setBusy]=useState(false);const [message,setMessage]=useState("");const [error,setError]=useState("");
  async function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();setBusy(true);setError("");const values=new FormData(event.currentTarget);
    const action=purpose==="verify"?"verify-email":code?"reset-password":"password-reset";
    try{
      const response=await fetch(`/api/account-access/${action}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(code?{code,...(purpose==="recover"?{password:values.get("password")}:{})}:{email:values.get("email")})});
      const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==="string"?data.detail:"No pudimos completar la solicitud.");
      setMessage(purpose==="verify"?"Tu correo quedó confirmado. Ya podés recibir las alertas.":code?"Tu contraseña quedó actualizada. Ingresá nuevamente a tu cuenta.":"Si el correo corresponde a una cuenta, recibirás un enlace para recuperar el acceso.");
      if(code)window.history.replaceState(null,"",purpose==="verify"?"/confirmar-correo":"/recuperar");
      window.dispatchEvent(new Event("mascomatch:session"));
    }catch(cause){setError(cause instanceof Error?cause.message:"No pudimos completar la solicitud.");}finally{setBusy(false);}
  }
  return <>{message?<p className="notice" role="status">{message}</p>:purpose==="verify"&&!code?<p>Pedí un enlace de confirmación desde tu cuenta.</p>:<form className="notification-login" onSubmit={submit}><fieldset className="section-fields" disabled={busy}>
    {purpose==="recover"&&(code?<label className="field-label">Nueva contraseña<input className="form-input" name="password" type="password" minLength={12} maxLength={128} required autoComplete="new-password"/><span className="field-help">Usá al menos 12 caracteres.</span></label>:<label className="field-label">Correo electrónico<input className="form-input" name="email" type="email" required autoComplete="email"/></label>)}
    <button className="button button-primary" type="submit">{busy?"Procesando…":purpose==="verify"?"Confirmar mi correo":code?"Guardar nueva contraseña":"Enviar enlace de recuperación"}</button>
  </fieldset></form>}{error&&<p role="alert" className="notice notice-warning">{error}</p>}<p><Link className="text-button" href="/mis-avisos">Ingresar a mi cuenta</Link></p></>;
}
