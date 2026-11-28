"use client";
import { ErrorState } from "../ui/error-state";
import { requestError } from "@/lib/request-error";
import { LoadingState } from "../ui/loading-state";
import {useEffect,useRef,useState} from "react";
import {createPortal} from "react-dom";
import type {Map as LeafletMap,LayerGroup} from "leaflet";
import {addLostMapMarker,lostMapLocations} from "@/lib/lost-map-marker";
import type {LostMapSelection} from "@/lib/lost-map-marker";
import {addObservationMapMarker,observationMapLocations} from "@/lib/observation-map-marker";
import type {ObservationMapSelection} from "@/lib/observation-map-marker";
import {LostLocationPreview} from "../lost-map-preview";
import {ObservationLocationPreview} from "./observation-preview";
import {MapReportCard} from "./map-report-card";
import type {MapReportPoint as Point} from "./map-report-card";
import {ALL_MAP_DISTANCES,COUNTRY_MAP_BOUNDS,DEFAULT_MAP_RADIUS_KM,MAX_MAP_RADIUS_KM,knownMapLocation,mapDateRangeError,mapSearchParams,parseMapRadius} from "@/lib/map-filters";
import type {MapOrigin} from "@/lib/map-filters";
import "./map-filters.css";
const API=(process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000/api/v1").replace(/\/$/,"");
const mapLayers=["lost","sighting"] as const;
type MapLayer=typeof mapLayers[number];
const layerClasses={lost:"map-layer-lost",sighting:"map-layer-sighting"};
const labels={lost:"Perdidos",sighting:"Avistamientos"};
function noticeFromMap(url:string){return `${url}${url.includes("?")?"&":"?"}origen=mapa`;}
type MapSelection={kind:"lost";data:LostMapSelection}|{kind:"observation";data:ObservationMapSelection};
export function CommunityMap(){
  const container=useRef<HTMLDivElement>(null);const map=useRef<LeafletMap|null>(null);const group=useRef<LayerGroup|null>(null);
  const [selection,setSelection]=useState<MapSelection|null>(null);
  const observationOpeners=useRef(new Map<string,()=>void>());
  const [ready,setReady]=useState(false);const [points,setPoints]=useState<Point[]>([]);const [species,setSpecies]=useState("");
  const [from,setFrom]=useState("");const [to,setTo]=useState("");const [radius,setRadius]=useState<number|null>(null);const [radiusInput,setRadiusInput]=useState("");
  const [compatible,setCompatible]=useState(false);const [center,setCenter]=useState<MapOrigin|null>(null);const [layers,setLayers]=useState<MapLayer[]>([...mapLayers]);
  const [error,setError]=useState("");const [busy,setBusy]=useState(false);const [refresh,setRefresh]=useState(0);const [locating,setLocating]=useState(false);const [locationError,setLocationError]=useState("");
  const locationOperation=useRef(0);const radiusRevision=useRef(0);const scopeTouched=useRef(false);
  const dateError=mapDateRangeError(from,to);
  const radiusError=radiusInput!==""&&parseMapRadius(radiusInput)===undefined?`Ingresá un número entre 0 y ${MAX_MAP_RADIUS_KM} km, o elegí «Todo el país».`:"";
  useEffect(()=>{
    let disposed=false;const request=locationOperation.current;
    void knownMapLocation(navigator).then(origin=>{if(!disposed&&origin&&request===locationOperation.current&&!scopeTouched.current){setCenter(origin);setRadius(DEFAULT_MAP_RADIUS_KM);}});
    return()=>{disposed=true;locationOperation.current+=1;};
  },[]);
  useEffect(()=>setRadiusInput(radius===null?"":String(radius)),[radius]);
  useEffect(()=>{
    let disposed=false;let observer:ResizeObserver|undefined;
    void import("leaflet").then(L=>{
      if(disposed||!container.current)return;
      const instance=L.map(container.current,{scrollWheelZoom:false}).fitBounds(COUNTRY_MAP_BOUNDS);map.current=instance;
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(instance).on("tileerror",()=>{if(!disposed)setError("No pudimos cargar algunas imágenes del mapa. Los reportes siguen disponibles en la lista.");});
      group.current=L.layerGroup().addTo(instance);observer=new ResizeObserver(()=>instance.invalidateSize({pan:false}));observer.observe(container.current);setReady(true);
    }).catch(()=>{if(!disposed)setError("No pudimos abrir el mapa. Los reportes siguen disponibles en la lista.");});
    return()=>{disposed=true;observer?.disconnect();map.current?.remove();map.current=null;group.current=null;};
  },[]);
  useEffect(()=>{
    if(dateError){setBusy(false);return;}
    const controller=new AbortController();setBusy(true);
    const timer=setTimeout(()=>{
      const params=mapSearchParams({species,from,to,radius,compatible,center});
      void fetch(`${API}/public/map?${params}`,{cache:"no-store",signal:controller.signal}).then(async response=>{
        if(!response.ok)throw new Error("No pudimos cargar los puntos. Intentá de nuevo.");
        const data=await response.json();if(!controller.signal.aborted){setPoints(data.points);setError("");}
      }).catch(cause=>{if(!controller.signal.aborted)setError(requestError(cause,"La consulta no pudo completarse. Intentá de nuevo en unos instantes."));}).finally(()=>{if(!controller.signal.aborted)setBusy(false);});
    },250);
    return()=>{clearTimeout(timer);controller.abort();};
  },[species,from,to,radius,compatible,center,refresh,dateError]);
  const visible=points.filter(point=>point.layer!=="found"&&layers.includes(point.layer));
  useEffect(()=>{
    if(!ready||!map.current||!group.current)return;
    let disposed=false;
    const cleanups:(()=>void)[]=[];
    void import("leaflet").then(L=>{
      if(disposed||!map.current||!group.current)return;
      group.current.clearLayers();setSelection(null);observationOpeners.current.clear();
      const filtered=points.filter(point=>point.layer!=="found"&&layers.includes(point.layer));
      const bounds:L.LatLngTuple[]=filtered.map(point=>[point.latitude,point.longitude]);
      for(const location of lostMapLocations(filtered.filter(point=>point.layer==="lost"))){
        cleanups.push(addLostMapMarker(L,map.current,group.current,location,
          next=>{if(!disposed)setSelection({kind:"lost",data:next});},
          content=>{if(!disposed)setSelection(current=>current?.data.content===content?null:current);},
        ));
      }
      const lostLocations=new Set(filtered.filter(point=>point.layer==="lost").map(point=>`${point.latitude},${point.longitude}`));
      for(const location of observationMapLocations(filtered.filter(point=>point.layer==="sighting"))){
        const handle=addObservationMapMarker(L,map.current,group.current,location,
          next=>{if(!disposed)setSelection({kind:"observation",data:next});},
          content=>{if(!disposed)setSelection(current=>current?.data.content===content?null:current);},
          lostLocations.has(`${location[0].latitude},${location[0].longitude}`)?64:0,
        );
        cleanups.push(handle.dispose);
        for(const point of location)observationOpeners.current.set(point.id,()=>handle.open(point.id));
      }
      if(center&&radius!==null){
        L.circle([center.latitude,center.longitude],{radius:radius*1000,color:"var(--accent-blue)",weight:1,fillOpacity:.04,interactive:false}).addTo(group.current);
        L.circleMarker([center.latitude,center.longitude],{radius:6,color:"var(--surface)",weight:2,fillColor:"var(--accent-blue)",fillOpacity:1}).bindTooltip("Tu ubicación").addTo(group.current);
        map.current.fitBounds(L.latLng(center.latitude,center.longitude).toBounds(Math.max(radius,1)*2000),{padding:[24,24],maxZoom:15});
      }else map.current.fitBounds([...COUNTRY_MAP_BOUNDS,...bounds],{padding:[24,24]});
    });
    return()=>{disposed=true;observationOpeners.current.clear();cleanups.forEach(cleanup=>cleanup());};
  },[points,layers,ready,center,radius]);
  function showObservation(point:Point){const open=observationOpeners.current.get(point.id);if(!open||!map.current)return;map.current.setView([point.latitude,point.longitude],Math.max(13,map.current.getZoom()),{animate:false});container.current?.scrollIntoView({block:"center"});open();}
  function chooseRadius(next:number|null){scopeTouched.current=true;radiusRevision.current+=1;setRadius(next);setRadiusInput(next===null?"":String(next));setLocationError("");}
  function nearby(){
    if(!navigator.geolocation||!window.isSecureContext){setLocationError("No pudimos usar la ubicación del dispositivo. Se muestran todas las zonas.");return;}
    scopeTouched.current=true;const request=++locationOperation.current;const revision=radiusRevision.current;setLocating(true);setLocationError("");
    navigator.geolocation.getCurrentPosition(position=>{if(request!==locationOperation.current)return;setCenter({latitude:position.coords.latitude,longitude:position.coords.longitude});if(revision===radiusRevision.current)setRadius(current=>current??DEFAULT_MAP_RADIUS_KM);setLocating(false);},()=>{if(request!==locationOperation.current)return;setLocationError("No pudimos actualizar tu ubicación. Podés revisar el permiso del navegador o seguir recorriendo el mapa.");setLocating(false);},{enableHighAccuracy:false,timeout:10000,maximumAge:300000});
  }
  return <><div className="map-filters">
      <label className="field-label">Mascota<select className="form-input" value={species} onChange={event=>setSpecies(event.target.value)}><option value="">Perros y gatos</option><option value="dog">Perros</option><option value="cat">Gatos</option></select></label>
      <fieldset className="map-date-filter" aria-describedby={dateError?"map-date-error":"map-date-help"}><legend className="field-label">Fecha del reporte</legend>
        <div className="map-date-fields"><label className="field-label">Desde<input className="form-input" type="date" value={from} max={to||undefined} aria-invalid={Boolean(dateError)} onChange={event=>setFrom(event.target.value)} /></label><label className="field-label">Hasta<input className="form-input" type="date" value={to} min={from||undefined} aria-invalid={Boolean(dateError)} onChange={event=>setTo(event.target.value)} /></label></div>
        {dateError?<p className="field-error" id="map-date-error" role="alert">{dateError} Corregí el rango para actualizar el mapa.</p>:<p className="field-help" id="map-date-help">{from||to?"Incluye ambos días, en horario de Uruguay.":"Sin fechas seleccionadas se muestran todos los reportes."}</p>}
        {(from||to)&&<button className="text-button map-clear-dates" type="button" onClick={()=>{setFrom("");setTo("");}}>Limpiar fechas</button>}
      </fieldset>
      <fieldset className="map-distance-filter" aria-describedby="map-distance-help"><legend className="field-label">Distancia desde mi ubicación</legend>
        <div className="map-distance-heading"><output htmlFor="map-distance-slider" className="map-distance-value">{radius===null?"Todo el país":`${radius} km`}</output><label className="map-distance-number"><span className="sr-only">Distancia en kilómetros</span><input className="form-input" type="text" inputMode="numeric" pattern="[0-9]*" maxLength={4} placeholder="Sin límite" value={radiusInput} aria-invalid={Boolean(radiusError)} aria-describedby={radiusError?"map-radius-error":"map-distance-help"} onChange={event=>{setRadiusInput(event.target.value);const next=parseMapRadius(event.target.value);if(next!==undefined)chooseRadius(next);}} onBlur={()=>{if(radiusInput==="")setRadiusInput(radius===null?"":String(radius));}} />{radiusInput!==""&&<span aria-hidden="true">km</span>}</label></div>
        <input id="map-distance-slider" className="map-distance-slider" type="range" min={0} max={ALL_MAP_DISTANCES} step={1} value={radius??ALL_MAP_DISTANCES} aria-label="Distancia desde mi ubicación" aria-valuetext={radius===null?"Todo el país":`${radius} kilómetros`} onChange={event=>{const value=Number(event.target.value);chooseRadius(value===ALL_MAP_DISTANCES?null:value);}} />
        <div className="map-distance-scale" aria-hidden="true"><span>0 km</span><span>Todo el país</span></div>
        {radiusError&&<p className="field-error" id="map-radius-error" role="alert">{radiusError}</p>}
        <p className="field-help" id="map-distance-help">{!center?"Sin tu ubicación se muestran todas las zonas. Elegí «Usar mi ubicación» para aplicar una distancia.":radius===null?"Mové el deslizador o escribí un número entre 0 y 500 km para buscar cerca de vos.":radius===0?"0 km busca reportes en el mismo punto de referencia. Los puntos públicos son aproximados.":"El radio se calcula desde tu ubicación. Los puntos públicos son aproximados."}</p>
      </fieldset>
    </div>
    <div className="location-actions map-location-actions"><button className="text-button" type="button" disabled={locating} onClick={nearby}>{locating?"Buscando ubicación…":center?"Actualizar mi ubicación":"Usar mi ubicación"}</button>{radius!==null&&<button type="button" className="text-button" onClick={()=>{locationOperation.current+=1;setLocating(false);chooseRadius(null);}}>Todo el país</button>}<button className="text-button" type="button" disabled={busy||Boolean(dateError)} onClick={()=>setRefresh(value=>value+1)}>Actualizar reportes</button></div>
    {locationError&&<p className="field-help" role="status">{locationError}</p>}
    <fieldset className="map-legend"><legend>Mostrar capas</legend>{mapLayers.map(layer=><label key={layer}><input type="checkbox" checked={layers.includes(layer)} onChange={event=>setLayers(current=>event.target.checked?[...current,layer]:current.filter(item=>item!==layer))}/><span aria-hidden="true" className={`map-legend-dot ${layerClasses[layer]}`} /> {labels[layer]}</label>)}</fieldset>
    <label className="sighting-recent"><input type="checkbox" checked={compatible} onChange={event=>setCompatible(event.target.checked)}/>Solo avistamientos con posibles coincidencias</label>
    {error&&<ErrorState compact title="No pudimos completar la consulta del mapa" description={error} />}{busy ? <LoadingState compact title="Cargando reportes en el mapa" /> : <p role="status">{visible.length} reportes en las capas seleccionadas</p>}
    <p className="field-help" id="community-map-help">Los círculos rojos son avisos de mascotas perdidas y los azules, avistamientos. Pasá el mouse o tocá una foto para ver su tarjeta. Las horas se muestran en horario de Uruguay.</p>
    <div ref={container} className="community-map" role="region" aria-label="Mapa de ubicaciones aproximadas" aria-describedby="community-map-help"/>
    {selection&&createPortal(selection.kind==="lost"?<LostLocationPreview key={selection.data.points[0].id} selection={selection.data} origin="mapa" onRefresh={()=>setRefresh(value=>value+1)}/>:<ObservationLocationPreview key={selection.data.selectedId} selection={selection.data} onRefresh={()=>setRefresh(value=>value+1)}/>,selection.data.content)}
    {!busy&&!visible.length&&<p>No hay reportes para estos filtros.</p>}<details className="map-report-list"><summary>Ver reportes en una lista</summary><ul className="map-report-grid" aria-label="Reportes en las capas seleccionadas">{visible.slice(0,100).map(point=><li key={`${point.layer}-${point.id}`}><MapReportCard point={point} href={point.url?noticeFromMap(point.url):undefined} onShowOnMap={point.layer==="sighting"&&ready?()=>showObservation(point):undefined}/></li>)}</ul>{visible.length>100&&<p>La lista muestra los primeros 100. Ajustá los filtros para ver menos resultados.</p>}</details>
  </>;
}
