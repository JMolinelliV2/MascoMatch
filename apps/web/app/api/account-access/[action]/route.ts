import { NextRequest, NextResponse } from "next/server";
import { authorization, boundedBody, sameOrigin, serverApi, SESSION_COOKIE } from "@/lib/server-api";
export async function POST(request:NextRequest,context:{params:Promise<{action:string}>}){
  const {action}=await context.params;
  if(!["request-verification","verify-email","password-reset","reset-password"].includes(action)||!sameOrigin(request))return NextResponse.json({detail:"Solicitud no permitida."},{status:403});
  try{
    const body=Buffer.from(await boundedBody(request,4096));
    const response=await fetch(`${serverApi}/auth/${action}`,{method:"POST",headers:{...authorization(request),"Content-Type":"application/json"},body,cache:"no-store",signal:AbortSignal.timeout(15000)});
    const data=await response.json();
    const result=NextResponse.json(data,{status:response.status,headers:{"Cache-Control":"no-store"}});
    const retry=response.headers.get("Retry-After");if(retry)result.headers.set("Retry-After",retry);
    if(response.ok&&(action==="reset-password"||(action==="verify-email"&&data.email_changed)))result.cookies.delete(SESSION_COOKIE);
    return result;
  }catch{return NextResponse.json({detail:"No pudimos completar la solicitud. Intentá de nuevo."},{status:503});}
}
