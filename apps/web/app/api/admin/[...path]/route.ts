import {NextRequest,NextResponse} from "next/server";
import {authorization,boundedBody,sameOrigin,serverApi} from "@/lib/server-api";
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
async function handle(request:NextRequest,context:{params:Promise<{path:string[]}>}){
  const {path}=await context.params;
  const read=request.method==="GET"&&((path.length===1&&["reports","overview"].includes(path[0]))||(path.length===2&&path[0]==="records"&&["users","pets","lost_cases","observations","matches"].includes(path[1])));
  const photo=request.method==="GET"&&path.length===4&&path[0]==="reports"&&uuid.test(path[1])&&path[2]==="photos"&&uuid.test(path[3]);
  const write=request.method==="PATCH"&&((path.length===2&&path[0]==="reports"&&uuid.test(path[1]))||(path.length===3&&path[0]==="publications"&&["lost_case","observation"].includes(path[1])&&uuid.test(path[2]))||(path.length===3&&path[0]==="users"&&uuid.test(path[1])&&path[2]==="status"));
  if((!read&&!write&&!photo)||(write&&!sameOrigin(request)))return NextResponse.json({detail:"Solicitud no permitida."},{status:403});
  try{const body=write?Buffer.from(await boundedBody(request,16384)):undefined;const query=read&&path[0]==="reports"?`?status=${encodeURIComponent(request.nextUrl.searchParams.get("status")??"OPEN")}`:"";const response=await fetch(`${serverApi}/admin/${path.join("/")}${query}`,{method:request.method,headers:{...authorization(request),...(write?{"Content-Type":"application/json"}:{})},body,cache:"no-store",signal:AbortSignal.timeout(15000)});if(photo&&response.ok)return new Response(response.body,{status:response.status,headers:{"Content-Type":response.headers.get("content-type")||"image/jpeg","Cache-Control":"no-store","X-Content-Type-Options":"nosniff"}});return NextResponse.json(await response.json(),{status:response.status,headers:{"Cache-Control":"no-store"}});}catch{return NextResponse.json({detail:"No pudimos consultar la administración."},{status:503});}
}
export const GET=handle;export const PATCH=handle;
