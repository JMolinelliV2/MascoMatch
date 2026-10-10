"use client";
import {useEffect,useRef,useState} from "react";
import {createPortal} from "react-dom";
import type {Map as LeafletMap,LayerGroup} from "leaflet";
import {addLostMapMarker,lostMapLocations} from "@/lib/lost-map-marker";
import type {LostMapSelection} from "@/lib/lost-map-marker";
import {LostLocationPreview} from "../lost-map-preview";
import {MapReportCard} from "./map-report-card";
import type {MapReportPoint as Point} from "./map-report-card";
const API=(process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000/api/v1").replace(/\/$/,"");
const colors={lost:"var(--text-primary)",sighting:"var(--primary)",found:"var(--success)"};
const layerClasses={lost:"map-layer-lost",sighting:"map-layer-sighting",found:"map-layer-found"};
const labels={lost:"Perdidos",sighting:"Avistamientos",found:"Encontrados"};
function noticeFromMap(url:string){return `${url}${url.includes("?")?"&":"?"}origen=mapa`;}
export function CommunityMap(){
  const container=useRef<HTMLDivElement>(null);const map=useRef<LeafletMap|null>(null);const group=useRef<LayerGroup|null>(null);
  const [selection,setSelection]=useState<LostMapSelection|null>(null);
  const [ready,setReady]=useState(false);const [points,setPoints]=useState<Point[]>([]);const [species,setSpecies]=useState("");const [days,setDays]=useState("30");const [radius,setRadius]=useState("15");const [compatible,setCompatible]=useState(false);const [center,setCenter]=useState<{latitude:number;longitude:number}|null>(null);const [layers,setLayers]=useState<Point["layer"][]>(["lost","sighting","found"]);const [error,setError]=useState("");const [busy,setBusy]=useState(false);const [refresh,setRefresh]=useState(0);
  useEffect(()=>{let disposed=false;void import("leaflet").then(L=>{if(disposed||!container.current)return;map.current=L.map(container.current,{scrollWheelZoom:false}).setView([-34.9,-56.16],11);L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(map.current).on("tileerror",()=>{if(!disposed)setError("No pudimos cargar algunas imágenes del mapa. Los reportes siguen disponibles en la lista.");});group.current=L.layerGroup().addTo(map.current);setReady(true);});return()=>{disposed=true;map.current?.remove();map.current=null;};},[]);
  useEffect(()=>{const controller=new AbortController();setBusy(true);const params=new URLSearchParams({species,days,radius_km:radius,compatible_only:String(compatible)});if(center){params.set("latitude",String(center.latitude));params.set("longitude",String(center.longitude));}void fetch(`${API}/public/map?${params}`,{cache:"no-store",signal:controller.signal}).then(async response=>{if(!response.ok)throw new Error("No pudimos cargar los puntos. Intentá de nuevo.");const data=await response.json();if(!controller.signal.aborted){setPoints(data.points);setError("");}}).catch(cause=>{if(!controller.signal.aborted)setError(cause.message);}).finally(()=>{if(!controller.signal.aborted)setBusy(false);});return()=>controller.abort();},[species,days,radius,compatible,center,refresh]);
  const visible=points.filter(point=>layers.includes(point.layer));
  useEffect(()=>{
    if(!ready||!map.current||!group.current)return;
    let disposed=false;
    const cleanups:(()=>void)[]=[];
    void import("leaflet").then(L=>{
      if(disposed||!map.current||!group.current)return;
      group.current.clearLayers();setSelection(null);
      const filtered=points.filter(point=>layers.includes(point.layer));
      const bounds:L.LatLngTuple[]=filtered.map(point=>[point.latitude,point.longitude]);
      for(const location of lostMapLocations(filtered.filter(point=>point.layer==="lost"))){
        cleanups.push(addLostMapMarker(L,map.current,group.current,location,
          next=>{if(!disposed)setSelection(next);},
          content=>{if(!disposed)setSelection(current=>current?.content===content?null:current);},
        ));
      }
      for(const point of filtered.filter(point=>point.layer!=="lost")){
        const content=document.createElement("div");
        const title=document.createElement("strong");title.textContent=point.title;content.append(title);
        const area=document.createElement("p");area.textContent=point.area||"Zona aproximada";content.append(area);
        if(point.url){const link=document.createElement("a");link.href=noticeFromMap(point.url);link.textContent="Ver aviso";content.append(link);}
        L.circleMarker([point.latitude,point.longitude],{radius:9,color:colors[point.layer],fillColor:colors[point.layer],fillOpacity:.8,weight:2}).addTo(group.current).bindPopup(content);
      }
      if(bounds.length)map.current.fitBounds(bounds,{padding:[32,32],maxZoom:13});
      else if(center)map.current.setView([center.latitude,center.longitude],12);
    });
    return()=>{disposed=true;cleanups.forEach(cleanup=>cleanup());};
  },[points,layers,ready,center]);
  function nearby(){if(!navigator.geolocation){setError("Tu navegador no ofrece ubicación. Podés recorrer el mapa manualmente.");return;}navigator.geolocation.getCurrentPosition(position=>setCenter({latitude:position.coords.latitude,longitude:position.coords.longitude}),()=>setError("No pudimos obtener tu ubicación. Revisá el permiso del navegador."),{timeout:15000,maximumAge:60000});}
  return <><div className="map-filters"><label className="field-label">Animal<select className="form-input" value={species} onChange={event=>setSpecies(event.target.value)}><option value="">Todos</option>{[["dog","Perros"],["cat","Gatos"],["rabbit","Conejos"],["bird","Aves"],["other","Otros"]].map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label><label className="field-label">Fecha<select className="form-input" value={days} onChange={event=>setDays(event.target.value)}><option value="7">Últimos 7 días</option><option value="30">Últimos 30 días</option><option value="90">Últimos 90 días</option><option value="0">Todas las fechas</option></select></label><label className="field-label">Radio cerca de mí<select className="form-input" value={radius} onChange={event=>setRadius(event.target.value)}><option value="5">5 km</option><option value="15">15 km</option><option value="30">30 km</option></select></label></div>
    <div className="location-actions"><button className="text-button" type="button" onClick={nearby}>Buscar cerca de mí</button>{center&&<button type="button" className="text-button" onClick={()=>setCenter(null)}>Ver todas las zonas</button>}<button className="text-button" type="button" onClick={()=>setRefresh(value=>value+1)}>Actualizar</button></div>
    <p className="field-help">El radio se aplica después de elegir “Buscar cerca de mí”. Los puntos aproximados no indican una dirección exacta.</p>
    <fieldset className="map-legend"><legend>Mostrar capas</legend>{(["lost","sighting","found"] as const).map(layer=><label key={layer}><input type="checkbox" checked={layers.includes(layer)} onChange={event=>setLayers(current=>event.target.checked?[...current,layer]:current.filter(item=>item!==layer))}/><span aria-hidden="true" className={`map-legend-dot ${layerClasses[layer]}`} /> {labels[layer]}</label>)}</fieldset>
    <label className="sighting-recent"><input type="checkbox" checked={compatible} onChange={event=>setCompatible(event.target.checked)}/>Solo avistamientos con posibles coincidencias</label>
    {error&&<p className="notice notice-warning" role="alert">{error}</p>}<p role="status">{busy?"Cargando puntos…":`${visible.length} reportes en las capas seleccionadas`}</p>
    <p className="field-help" id="community-map-help">Pasá el mouse sobre una foto o tocala para ver la miniatura del animal perdido y abrir su aviso.</p>
    <div ref={container} className="community-map" role="region" aria-label="Mapa de ubicaciones aproximadas" aria-describedby="community-map-help"/>
    {selection&&createPortal(<LostLocationPreview key={selection.points[0].id} selection={selection} origin="mapa" onRefresh={()=>setRefresh(value=>value+1)}/>,selection.content)}
    {!busy&&!visible.length&&<p>No hay reportes para estos filtros.</p>}<details className="map-report-list"><summary>Ver reportes en una lista</summary><ul className="map-report-grid" aria-label="Reportes en las capas seleccionadas">{visible.slice(0,100).map(point=><li key={`${point.layer}-${point.id}`}><MapReportCard point={point} href={point.url?noticeFromMap(point.url):undefined}/></li>)}</ul>{visible.length>100&&<p>La lista muestra los primeros 100. Ajustá los filtros para ver menos resultados.</p>}</details>
  </>;
}
