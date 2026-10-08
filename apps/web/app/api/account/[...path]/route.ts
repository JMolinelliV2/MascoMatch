import { NextRequest, NextResponse } from "next/server";
import { authorization, boundedBody, sameOrigin, serverApi } from "@/lib/server-api";
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
async function handle(request:NextRequest,context:{params:Promise<{path:string[]}>}) {
  const {path}=await context.params;
  const method=request.method;
  const dashboard=method==="GET" && path.length===1 && path[0]==="dashboard";
  const report=path.length===2 && ["lost-cases","observations","pets"].includes(path[0]) && uuid.test(path[1]) && ["GET","PATCH","DELETE"].includes(method);
  const upload=method==="POST" && path.join("/")==="photos/upload";
  const edit=method==="PATCH" && path.length===2 && path[0]==="cases" && uuid.test(path[1]);
  if ((!dashboard&&!report&&!upload&&!edit) || (method!=="GET"&&!sameOrigin(request))) return NextResponse.json({detail:"Solicitud no permitida."},{status:403});
  try {
    const body=method==="PATCH"||upload ? Buffer.from(await boundedBody(request,upload?11*1024*1024:16384)):undefined;
    const response=await fetch(`${serverApi}/${dashboard?"me/dashboard":edit?`me/cases/${path[1]}`:path.join("/")}`,{method,headers:{...authorization(request),...(body?{"Content-Type":request.headers.get("content-type")||"application/json"}:{})},body,cache:"no-store",signal:AbortSignal.timeout(30000)});
    if(response.status===204)return new Response(null,{status:204});
    return NextResponse.json(await response.json(),{status:response.status,headers:{"Cache-Control":"no-store"}});
  } catch {return NextResponse.json({detail:"No pudimos guardar los cambios."},{status:503});}
}
export const GET=handle;
export const PATCH=handle;
export const DELETE=handle;
export const POST=handle;
