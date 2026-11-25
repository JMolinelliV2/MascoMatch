import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import ts from "typescript";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

const require = createRequire(import.meta.url);
async function compiled(name, imports = {}, sourceFile = new URL(`../app/ui/${name}.tsx`, import.meta.url)) {
  const source = await readFile(sourceFile, "utf8");
  let { outputText } = ts.transpileModule(source, { compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } });
  for (const [specifier, target] of Object.entries({ react: pathToFileURL(require.resolve("react")).href, "react/jsx-runtime": pathToFileURL(require.resolve("react/jsx-runtime")).href, ...imports })) {
    outputText = outputText.replaceAll(JSON.stringify(specifier), JSON.stringify(target));
  }
  return `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`;
}
const pictogram = await compiled("pictogram");
const { Stepper } = await import(await compiled("stepper", { "./pictogram": pictogram }));
const { MatchScore } = await import(await compiled("match-score"));
const { SexSelector } = await import(await compiled("sex-selector", { "./pictogram": pictogram }));
const reportPhotos = await compiled("report-photos", {}, new URL("../lib/report-photos.ts", import.meta.url));
const { PhotoUploader } = await import(await compiled("photo-uploader", { "./pictogram": pictogram, "@/lib/report-photos": reportPhotos }));
const moduleUrl = source => `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
const link = moduleUrl(`import {createElement} from ${JSON.stringify(pathToFileURL(require.resolve("react")).href)}; export default function Link(props) {return createElement("a",props);}`);
const reviewRequest = moduleUrl("export function ReviewRequest(){return null;}");
const loginReturn = await compiled("login-return", {}, new URL("../lib/login-return.ts", import.meta.url));
const { MarkRecovered, OwnerRecoveryLogin, RecoverySuccess } = await import(await compiled("owner-recovery", { "./pictogram": pictogram, "next/link": link, "../review-request": reviewRequest, "@/lib/login-return": loginReturn }));
const { ReviewIdentity } = await import(await compiled("review-identity"));
const { ReviewSummary } = await import(await compiled("review-summary"));
const phoneNumbers = await compiled("phone-numbers", { "libphonenumber-js/max": import.meta.resolve("libphonenumber-js/max") }, new URL("../lib/phone-numbers.ts", import.meta.url));
const { PhoneField } = await import(await compiled("phone-field", { "@/lib/phone-numbers": phoneNumbers }));
const errorStateModule = await compiled("error-state", { "./pictogram": pictogram });
const { ErrorState } = await import(errorStateModule);
const { default: PageError } = await import(await compiled("page-error", { "./ui/error-state": errorStateModule }, new URL("../app/error.tsx", import.meta.url)));
const { default: NotFound } = await import(await compiled("not-found", { "./ui/error-state": errorStateModule, "next/link": link }, new URL("../app/not-found.tsx", import.meta.url)));
const html = (component, props) => renderToStaticMarkup(createElement(component, props));

test("el error de pantalla muestra la mascota estática, el contexto accesible y un reintento explícito", () => {
  let retries = 0;
  const markup = html(ErrorState, { title: "No pudimos consultar tu cuenta", description: "Reintentá para continuar con tu aviso.", headingLevel: 1, onRetry() { retries++; } });
  assert.equal(retries, 0);
  assert.match(markup, /role="alert"/);
  assert.match(markup, /<h1[^>]*>No pudimos consultar tu cuenta<\/h1>/);
  assert.match(markup, /src="\/images\/error-dog\.webp(?:\?[^\"]*)?"/);
  assert.match(markup, /alt=""/);
  assert.match(markup, /<button[^>]*type="button"/);
  assert.match(markup, /Reintentar/);
  const titleId = markup.match(/aria-labelledby="([^"]+)"/)[1];
  const descriptionId = markup.match(/aria-describedby="([^"]+)"/)[1];
  assert.ok(markup.includes(`id="${titleId}"`));
  assert.ok(markup.includes(`id="${descriptionId}"`));
  assert.doesNotMatch(markup, /<form|loading-dog|<animate|role="status"/);
});

test("un error de sección conserva su contexto sin forzar navegación ni un formulario", () => {
  const markup = html(ErrorState, { compact: true, headingLevel: 3, title: "No pudimos abrir las fotos", description: '<script>alert("privado")</script>' });
  assert.match(markup, /masco-error--compact/);
  assert.match(markup, /<h3/);
  assert.match(markup, /&lt;script&gt;/);
  assert.doesNotMatch(markup, /<script|<button|<a |<form/);
});

test("el reintento en curso se anuncia y queda deshabilitado", () => {
  const markup = html(ErrorState, { compact: true, retrying: true, onRetry() {} });
  assert.match(markup, /<button[^>]*disabled=""/);
  assert.match(markup, /Reintentando…/);
});

test("la página inexistente permite consultar los avisos sin fingir un error de sesión", () => {
  const markup = html(NotFound);
  assert.match(markup, /No encontramos esta página/);
  assert.match(markup, /href="\/perdidos"/);
  assert.match(markup, /Ver mascotas reportadas/);
  assert.doesNotMatch(markup, /Reintentar|<form/);
});

test("el error inesperado no publica detalles internos y ofrece el reinicio de esa pantalla", () => {
  const markup = html(PageError, { error: Object.assign(new Error("SECRET_INTERNAL_DATA"), { digest: "PRIVATE_DIGEST" }), reset() {} });
  assert.match(markup, /No pudimos abrir esta página/);
  assert.match(markup, /Reintentar/);
  assert.doesNotMatch(markup, /SECRET_INTERNAL_DATA|PRIVATE_DIGEST/);
});

test("el campo de teléfono explica el formato y conserva los contratos opcional y obligatorio", () => {
  const optional = html(PhoneField, { value: "099 123 456" });
  assert.match(optional, /type="tel"/);
  assert.match(optional, /inputMode="tel"/);
  assert.match(optional, /name="phone"/);
  assert.match(optional, /Uruguay: 099 123 456/);
  assert.match(optional, /Otros países/);
  assert.doesNotMatch(optional, /required=""/);
  const required = html(PhoneField, { name: "finder_phone", label: "Teléfono de contacto", required: true });
  assert.match(required, /required=""/);
  assert.match(required, /name="finder_phone"/);
});

test("el stepper conserva las tres etapas y comunica la etapa actual", () => {
  const markup = html(Stepper, { steps: ["Mascota", "Fecha y lugar", "Contacto y revisión"], current: 2 });
  assert.equal((markup.match(/<li /g) || []).length, 3);
  assert.match(markup, /aria-current="step"/);
  assert.match(markup, /value="2" max="3"/);
  assert.match(markup, /completado/);
});
test("el selector visual conserva el campo sex y el valor unknown del contrato actual", () => {
  const markup = html(SexSelector);
  assert.match(markup, /<select name="sex"/);
  assert.match(markup, /value="unknown" selected=""/);
  assert.equal((markup.match(/type="radio"/g) || []).length, 3);
});
test("una compatibilidad alta tiene contexto y no se expresa como probabilidad de identidad", () => {
  const markup = html(MatchScore, { score: .92 });
  assert.match(markup, /92%/);
  assert.match(markup, /Compatibilidad alta/);
  assert.doesNotMatch(markup, /probabilidad/i);
});
test("la compatibilidad inferior se presenta para revisión", () => {
  assert.match(html(MatchScore, { score: .71 }), /Para revisar/);
});
test("un score ausente o inválido no produce un porcentaje inventado", () => {
  assert.equal(html(MatchScore, { score: undefined }), "");
  assert.equal(html(MatchScore, { score: NaN }), "");
});
test("el formulario general permite cinco fotos opcionales con los formatos actuales", () => {
  const markup = html(PhotoUploader, { name: "photo" });
  assert.match(markup, /name="photo"/);
  assert.match(markup, /image\/jpeg,image\/png,image\/webp/);
  assert.match(markup, /10 MB/);
  assert.match(markup, /multiple=""/);
  assert.doesNotMatch(markup, /required=""/);
});
test("el avistamiento vinculado conserva el control photos y permite cinco fotos opcionales", () => {
  const markup = html(PhotoUploader, { name: "photos", label: "Fotos", maxFiles: 5 });
  assert.match(markup, /name="photos"/);
  assert.match(markup, /multiple=""/);
  assert.match(markup, /Hasta 5 fotos/);
  assert.doesNotMatch(markup, /required=""/);
});

test("el dueño puede marcar la recuperación sin un formulario, fotos ni datos de contacto", () => {
  const markup = html(MarkRecovered, { caseId: "owned-case", onRecovered() {} });
  assert.match(markup, /Ya la tengo conmigo/);
  assert.match(markup, /type="button"/);
  assert.doesNotMatch(markup, /<form|<input|<textarea|<select|required=/);
});

test("el dueño sin sesión puede ingresar sin enviar el formulario y regresar al aviso concreto", () => {
  const caseId = "ca11e123-1234-4321-a123-123456789012";
  const markup = html(OwnerRecoveryLogin, { caseId });
  assert.match(markup, /Soy el dueño del aviso/);
  const url = new URL(markup.match(/href="([^"]+)"/)[1], "https://mascomatch.com");
  assert.equal(url.pathname, "/login");
  assert.equal(url.searchParams.get("next"), `/encontre?aviso=${caseId}`);
  assert.doesNotMatch(markup, /<form|<button|<input|required=/);
});

test("la confirmación de recuperación informa el cierre de la búsqueda sin esperar una comparación", () => {
  const markup = html(RecoverySuccess, { caseId: "owned-case", name: "Luna" });
  assert.match(markup, /¡Luna volvió a casa!/);
  assert.match(markup, /marcado como encontrado/);
  assert.match(markup, /búsqueda está cerrada/);
  assert.doesNotMatch(markup, /<form|<input|<textarea|<select|required=|pendiente de revisión/i);
});

test("la identidad de la reseña permite anonimato o el nombre de cuenta sin apodo libre", () => {
  const markup = html(ReviewIdentity, { id: "identity", accountName: "Julian M.", anonymous: true, onChange() {} });
  assert.equal((markup.match(/type="radio"/g) || []).length, 2);
  assert.match(markup, /Anónimo/);
  assert.match(markup, /Julian M\./);
  const selected = markup.match(/<input[^>]*>/g).filter(input => input.includes('checked=""'));
  assert.equal(selected.length, 1);
  assert.match(selected[0], /value="anonymous"/);
  assert.doesNotMatch(markup, /type="text"|<textarea|apodo/i);
  const named = html(ReviewIdentity, { id: "identity", accountName: "Julian M.", anonymous: false, onChange() {} });
  const namedSelected = named.match(/<input[^>]*>/g).filter(input => input.includes('checked=""'));
  assert.equal(namedSelected.length, 1);
  assert.match(namedSelected[0], /value="account"/);
});

test("la reseña previa conserva estrellas, comentario y estado de publicación para revisarla", () => {
  const review = { id: "review", rating: 4, comment: "Mi experiencia anterior que puedo mantener o editar.", display_name: "Julian M.", visibility: "WITHDRAWN" };
  const markup = html(ReviewSummary, { review });
  assert.match(markup, /4 de 5 estrellas/);
  assert.match(markup, /Mi experiencia anterior que puedo mantener o editar\./);
  assert.match(markup, /está retirada/);
  assert.doesNotMatch(markup, /<input|<textarea/);
});
