// Run only against the explicitly disposable production preview, with SMTP disabled.
import assert from "node:assert/strict";
import {randomUUID} from "node:crypto";
import {readFile} from "node:fs/promises";

assert.equal(process.env.DISPOSABLE_STACK,"mascomatch-prod-smoke","Use only the explicitly disposable preview stack");
assert.equal(process.env.NODE_ENV,"production","Requires the production web image");

const base="http://localhost:3000";
const identity=randomUUID();
const email=`smoke-owner-${identity}@example.test`;
const password="test-only-production-passphrase";
let cookie="";
async function request(path,body,method=body?"POST":"GET"){
  const response=await fetch(base+path,{method,headers:{Origin:"https://mascomatch.com",...(cookie?{Cookie:cookie}:{}),...(body?{"Content-Type":"application/json"}:{})},body:body?JSON.stringify(body):undefined});
  const data=await response.json();
  assert.equal(response.ok,true,`${path}: HTTP ${response.status}`);
  return {response,data};
}
const session=await request("/api/session",{mode:"register",email,password,name:"Cuenta sintética de producción"});
assert.equal(session.data.access_token,undefined);
assert.equal(session.data.user.email_verification_required,true);
const header=session.response.headers.get("set-cookie");
assert.match(header,/__Host-mascomatch_session=/);
assert.match(header,/HttpOnly/i);assert.match(header,/Secure/i);assert.match(header,/SameSite=Lax/i);
cookie=header.split(";")[0];
const pet=(await request("/api/backend/pets",{name:"Animal sintético",species:"dog",sex:"female",primary_color:"brown",size:"medium"})).data;
const lost=(await request("/api/backend/lost-cases",{pet_id:pet.id,lost_at:new Date(Date.now()-3600000).toISOString(),latitude:-34.9,longitude:-56.1,description:"Aviso sintético de la prueba de producción",public_location:"Montevideo"})).data;
const form=new FormData();
form.set("owner_type","lost_case");form.set("owner_id",lost.id);
form.set("file",new Blob([await readFile("/app/public/images/dog-hero.jpg")],{type:"image/jpeg"}),"example.jpg");
const upload=await fetch(base+"/api/backend/photos/upload",{method:"POST",headers:{Cookie:cookie,Origin:"https://mascomatch.com"},body:form});
assert.equal(upload.status,201);
const photo=await upload.json();assert.equal(photo.signed_url,undefined);
const dashboard=(await request("/api/account/dashboard")).data;
assert.equal(dashboard.cases.length,1);
assert.equal((await fetch(base+"/api/backend/pets",{method:"POST",headers:{Origin:"https://other.example","Content-Type":"application/json"},body:"{}"})).status,403);
await request("/api/session",undefined,"DELETE");
const after=await request("/api/session");assert.equal(after.data.user,null);
console.log(JSON.stringify({bff_signup:true,token_not_exposed:true,secure_cookie:true,case_saved:true,photo_saved:true,csrf_rejected:true,logout_revoked:true,case_id:lost.id,photo_id:photo.photo.id,email}));
