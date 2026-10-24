// Verkaufte Preise (ebay.de, Stand 24.10.2026 verifiziert): im ebay.de-Tab per javascript_tool ausfuehren (nicht awaited async-IIFE, Ergebnis window.__o).
// Q = {sku:["Suchtext","wort1,wort2"]}; Treffer muessen ALLE Woerter (kleingeschrieben) im Titel haben (Nachname + Nenner/Setwort). textContent hat KEINE Leerzeichen zwischen Feldern.
window.__o={};window.__d=0;
(async()=>{for(const [k,[q,f]] of Object.entries(Q)){try{
 const r=await fetch('/sch/i.html?_nkw='+encodeURIComponent(q)+'&_sacat=261328&LH_Sold=1&LH_Complete=1&_ipg=60');
 const d=new DOMParser().parseFromString(await r.text(),'text/html');const it=[];
 d.querySelectorAll('li.s-card').forEach(li=>{const t=li.textContent.replace(/\s+/g,' ');
  const m=t.match(/Verkauft (\d+\. \w+ \d{4})(.*?)Wird in neuem.*?EUR (\d+),(\d\d)/);if(!m)return;
  const tl=m[2].toLowerCase();if(f.split(',').every(w=>tl.includes(w)))it.push([+(m[3]+'.'+m[4]),m[1],m[2].slice(0,80)])});
 it.sort((a,b)=>a[0]-b[0]);window.__o[k]={n:it.length,med:it.length?it[Math.floor(it.length/2)][0]:null,min:it[0]&&it[0][0],max:it.length&&it[it.length-1][0],s:it.slice(-3)}
}catch(e){window.__o[k]={err:String(e)}}await new Promise(r=>setTimeout(r,500))}window.__d=1})();
