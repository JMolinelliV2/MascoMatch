import {NextRequest,NextResponse} from "next/server";
import {authorization,boundedBody,sameOrigin,serverApi} from "@/lib/server-api";
export async function POST(request:NextRequest){
  if(!sameOrigin(request))return NextResponse.json({detail:"Solicitud no permitida."},{status:403});
  try{const body=Buffer.from(await boundedBody(request,4096));const response=await fetch(`${serverApi}/reports`,{method:"POST",headers:{...authorization(request),"Content-Type":"application/json"},body,cache:"no-store",signal:AbortSignal.timeout(10000)});return NextResponse.json(await response.json(),{status:response.status,headers:{"Cache-Control":"no-store"}});}catch{return NextResponse.json({detail:"No pudimos enviar la denuncia."},{status:503});}
}
