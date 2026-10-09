"use client";
import {useEffect,useState} from "react";
import Link from "next/link";
import {VerifyEmailNotice} from "./verify-email-notice";
import type {FormEvent,ReactNode} from "react";
export type SessionUser={id:string;name:string;role?:string;email_verified?:boolean;email_verification_required?:boolean};
export function AccountSession({children}:{children:(user:SessionUser)=>ReactNode}) {
  const [user,setUser]=useState<SessionUser|null>(null);
  const [checking,setChecking]=useState(true);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  useEffect(()=>{const controller=new AbortController();void fetch("/api/session",{cache:"no-store",signal:controller.signal}).then(async response=>{if(!response.ok)throw new Error("No pudimos consultar tu sesión.");const data=await response.json();if(!controller.signal.aborted)setUser(data.user);}).catch(cause=>{if(!controller.signal.aborted)setError(cause.message);}).finally(()=>{if(!controller.signal.aborted)setChecking(false);});return()=>controller.abort();},[]);
  async function login(event:FormEvent<HTMLFormElement>) {
    event.preventDefault();setBusy(true);setError("");const form=event.currentTarget;const values=new FormData(form);
    try {const response=await fetch("/api/session",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({mode:"login",email:values.get("email"),password:values.get("password")})});const data=await response.json();if(!response.ok)throw new Error("El correo o la contraseña no son correctos.");form.reset();setUser(data.user);window.dispatchEvent(new Event("mascomatch:session"));}
    catch(cause){setError(cause instanceof Error?cause.message:"No pudimos iniciar sesión.");}finally{setBusy(false);}
  }
  async function logout(){const response=await fetch("/api/session",{method:"DELETE"});if(response.ok){setUser(null);window.dispatchEvent(new Event("mascomatch:session"));}else setError("No pudimos cerrar tu sesión.");}
  if(checking)return <p role="status">Consultando tu sesión…</p>;
  return <>{user?<><div className="notifications-account"><span>{user.name}</span><button className="text-button" type="button" onClick={()=>void logout()}>Cerrar sesión</button></div>{user.email_verification_required&&!user.email_verified&&<VerifyEmailNotice/>}{children(user)}</>:<form onSubmit={login} className="notification-login"><h2>Ingresá con tu cuenta</h2><fieldset disabled={busy} className="section-fields"><label className="field-label">Correo electrónico<input className="form-input" name="email" type="email" required autoComplete="email"/></label><label className="field-label">Contraseña<input className="form-input" name="password" type="password" required autoComplete="current-password"/></label><button className="button button-primary" type="submit">{busy?"Ingresando…":"Ingresar"}</button></fieldset><p><Link className="text-button" href="/recuperar">Olvidé mi contraseña</Link></p></form>}{error&&<p className="notice notice-warning" role="alert">{error}</p>}</>;
}
