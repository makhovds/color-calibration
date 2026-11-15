"""Offline dataset controls for the chromaticity plot. Автономная интерактивная диаграмма."""

import base64
import html
import json
import numpy as np
from . import gamut, spectra
from .workflow import coverage_table, LABELS

COLORS = [
    "#172e4c",
    "#ab4dc3",
    "#159fbc",
    "#b88c19",
    "#e66b3f",
    "#1f8a65",
    "#7e64bc",
    "#be5973",
    "#68737e",
]


def background_mesh(config):
    """Cache the display surface. Сохранить поверхность цветного фона."""
    from .chromaticity import chromaticity_mesh

    path = config.artifacts / "observers/chromaticity_mesh.npz"
    if not path.exists():
        x, y, rgb = chromaticity_mesh(
            spectra.load_cmf(config.artifacts / "observers", "2_1931")
        )
        np.savez_compressed(path, x=x, y=y, rgb=rgb)
    with np.load(path) as mesh:
        return mesh["x"], mesh["y"], mesh["rgb"]


def background_image(config):
    """Cache the independent chromaticity background. Сохранить независимый цветной фон."""
    import matplotlib.pyplot as plt
    from .chromaticity import chromaticity_mesh, draw_chromaticity

    target = config.artifacts / "observers/chromaticity_background.png"
    if not target.exists():
        fig = plt.figure(figsize=(6, 6), dpi=150)
        ax = fig.add_axes((0, 0, 1, 1))
        draw_chromaticity(ax, background_mesh(config))
        ax.set_axis_off()
        fig.savefig(target, dpi=150)
        plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(target.read_bytes()).decode()


def create_explorer(config, datasets, profile="historical", language="en"):
    """Export and embed the same interactive figure; no server or widget extension required."""
    ru = language == "ru"
    payload = {
        "language": language,
        "profile": profile,
        "background": background_image(config),
        "datasets": [],
    }
    for i, (key, item) in enumerate(datasets.items()):
        payload["datasets"].append(
            {
                "key": key,
                "label": LABELS[key][int(ru)],
                "color": COLORS[i],
                "names": (
                    [f"Вершина {j}" for j in (1, 2, 3)]
                    if ru and key == "ccd"
                    else item["names"]
                ),
                "xy": np.asarray(item["xy"]).tolist(),
                "hull": gamut.convex_hull(item["xy"]).tolist(),
            }
        )
    payload["metrics"] = {
        key: coverage_table(datasets, key).to_dict("records") for key in datasets
    }
    template = r"""<!doctype html><html lang="__LANG__"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>__TITLE__</title>
<style>
*{box-sizing:border-box}body{margin:0;padding:22px;background:#f6f8fb;color:#17314b;font:15px system-ui,sans-serif}
main{max-width:1140px;margin:auto;background:white;border:1px solid #dce4ed;border-radius:16px;padding:24px}
h1{font-size:25px;margin:0 0 7px}p{line-height:1.5;color:#51687e}.layout{display:grid;grid-template-columns:minmax(0,2.2fr) minmax(250px,1fr);gap:20px}
svg{width:100%;height:auto;display:block}.controls{padding:12px;background:#f4f7fa;border-radius:10px;align-self:start}
label,button,select{cursor:pointer}select,button{font:inherit;border:1px solid #c4d1df;border-radius:6px;padding:7px;background:white;color:#17314b}
select{width:100%;margin:8px 0 12px}.toggle{display:grid;grid-template-columns:1fr 45px 45px;gap:5px;padding:8px 0;border-top:1px solid #e1e7ef;align-items:center}
.toggle input{width:17px;height:17px;accent-color:#227c92}.toggle span{font-size:13px}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}
.buttons{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}button:hover{background:#eaf1f6}.table-wrap{overflow:auto;margin-top:18px}
table{width:100%;border-collapse:collapse;text-align:right;font-variant-numeric:tabular-nums}th,td{padding:10px;border-bottom:1px solid #e3e9ef}th:first-child,td:first-child{text-align:left}th{font-size:12px;color:#526b82}
.note{font-size:12px;margin-bottom:0}.reference{font-weight:650;background:#eff6fa}@media(max-width:760px){body{padding:8px}main{padding:12px}.layout{grid-template-columns:1fr}h1{font-size:21px}}
</style></head><body><main><h1 id="title"></h1><p id="intro"></p><div class="layout">
<svg id="plot" viewBox="0 0 720 720" role="img" aria-label="__TITLE__"></svg>
<div class="controls"><label id="reference-label" for="reference"></label><select id="reference"></select>
<div class="toggle"><span id="dataset-label"></span><span id="points-label"></span><span id="hull-label"></span></div><div id="toggles"></div>
<div class="buttons"><button id="all"></button><button id="none"></button><button id="save"></button></div></div></div>
<div class="table-wrap"><table><thead><tr id="head"></tr></thead><tbody id="metrics"></tbody></table></div><p class="note" id="note"></p></main>
<script>
const data=__PAYLOAD__, ru=data.language==='ru', ns='http://www.w3.org/2000/svg';
const text=(en,ruText)=>ru?ruText:en, $=id=>document.getElementById(id);
$('title').textContent=text('Chromaticity explorer','Интерактивная диаграмма цветности');
$('intro').textContent=text('Choose datasets, points and hulls. The table uses the selected reference hull.','Выберите точки и оболочки наборов данных. Таблица рассчитывается относительно выбранной оболочки.');
$('reference-label').textContent=text('Reference hull','Эталонная оболочка');$('dataset-label').textContent=text('Dataset','Набор');
$('points-label').textContent=text('Points','Точки');$('hull-label').textContent=text('Hull','Охват');
$('all').textContent=text('Show all','Показать все');$('none').textContent=text('Hide all','Скрыть все');$('save').textContent=text('Save SVG','Сохранить SVG');
$('note').textContent=text('Coverage = area(intersection) / area(reference hull). The CCD triangle is an approximate response-based construction, not a calibrated physical camera gamut. Research coordinates: D50; background: CIE 1931 / D65.','Покрытие = площадь пересечения / площадь эталонной оболочки. Треугольник CCD — приближенная конструкция по откликам, а не физически откалиброванный охват камеры. Координаты: D50; фон: CIE 1931 / D65.');
const headers=ru?['Набор','Точки','Площадь xy','Покрытие, %','Точек / площадь']:['Dataset','Points','xy area','Coverage, %','Points / area'];
headers.forEach(s=>{const n=document.createElement('th');n.textContent=s;$('head').append(n)});
const state={};
data.datasets.forEach(d=>{const o=document.createElement('option');o.value=d.key;o.textContent=d.label;$('reference').append(o);
 const row=document.createElement('div');row.className='toggle';const label=document.createElement('span');
 const dot=document.createElement('i');dot.className='dot';dot.style.background=d.color;label.append(dot,document.createTextNode(d.label));row.append(label);
 state[d.key]={points:['ccd','prototype'].includes(d.key),hull:['ccd','prototype','dyes','kodak-q60'].includes(d.key)};
 ['points','hull'].forEach(kind=>{const check=document.createElement('input');check.type='checkbox';check.checked=state[d.key][kind];check.id=d.key+'-'+kind;check.setAttribute('aria-label',d.label+' '+(kind==='points'?text('points','точки'):text('hull','оболочка')));check.onchange=()=>{state[d.key][kind]=check.checked;update()};row.append(check)});
 $('toggles').append(row);
});
$('reference').value='ccd';$('reference').onchange=update;
function svg(tag,attributes,parent=$('plot')){const e=document.createElementNS(ns,tag);Object.entries(attributes).forEach(([k,v])=>e.setAttribute(k,v));parent.append(e);return e}
const X=x=>58+x/0.85*630,Y=y=>660-y/0.85*630;
function polygon(points,color,dashed=false){return svg('polygon',{points:points.map(p=>X(p[0])+','+Y(p[1])).join(' '),fill:'none',stroke:color,'stroke-width':dashed?2.5:2,'stroke-dasharray':dashed?'7 5':'','clip-path':'url(#clip)'})}
function update(){const plot=$('plot');plot.replaceChildren();const defs=svg('defs',{});const clip=svg('clipPath',{id:'clip'},defs);svg('rect',{x:58,y:30,width:630,height:630},clip);
 svg('image',{href:data.background,x:58,y:30,width:630,height:630});
 for(let v=0;v<=8;v++){const n=v/10;svg('line',{x1:X(n),x2:X(n),y1:30,y2:660,stroke:'#75899b','stroke-opacity':.15});svg('line',{x1:58,x2:688,y1:Y(n),y2:Y(n),stroke:'#75899b','stroke-opacity':.15});
 const tx=svg('text',{x:X(n),y:685,'text-anchor':'middle','font-size':13});tx.textContent=n.toFixed(1);const ty=svg('text',{x:45,y:Y(n)+4,'text-anchor':'end','font-size':13});ty.textContent=n.toFixed(1)}
 svg('rect',{x:58,y:30,width:630,height:630,fill:'none',stroke:'#405366'});svg('text',{x:375,y:713,'text-anchor':'middle','font-size':17}).textContent='x';svg('text',{x:17,y:350,'font-size':17}).textContent='y';
 const reference=$('reference').value;
 data.datasets.forEach(d=>{if(state[d.key].hull)polygon(d.hull,d.color);if(state[d.key].points)d.xy.forEach((p,i)=>{const c=svg('circle',{cx:X(p[0]),cy:Y(p[1]),r:d.key==='ccd'?5:3.4,fill:d.color,'fill-opacity':.7,stroke:d.color,'stroke-width':.6,'clip-path':'url(#clip)'});svg('title',{},c).textContent=d.label+' · '+d.names[i]+' ('+p.map(v=>v.toFixed(4)).join(', ')+')'})});
 polygon(data.datasets.find(d=>d.key===reference).hull,'#172e4c',true);
 const white=[.96419865576090,1,.82511648322104],sum=white.reduce((a,b)=>a+b);const c=svg('circle',{cx:X(white[0]/sum),cy:Y(white[1]/sum),r:4,fill:'#d94141'});svg('title',{},c).textContent='D50';
 $('metrics').replaceChildren();data.metrics[reference].forEach(m=>{if(!(state[m.dataset].points||state[m.dataset].hull||m.dataset===reference))return;
 const tr=document.createElement('tr');if(m.dataset===reference)tr.className='reference';const d=data.datasets.find(d=>d.key===m.dataset);
 [d.label,m.points,m.xy_area.toFixed(6),m.reference_coverage_percent.toFixed(4),m.points_per_xy_area.toFixed(2)].forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.append(td)});$('metrics').append(tr)});
}
function showAll(value){data.datasets.forEach(d=>['points','hull'].forEach(k=>{state[d.key][k]=value;$(d.key+'-'+k).checked=value}));update()}
$('all').onclick=()=>showAll(true);$('none').onclick=()=>showAll(false);
$('save').onclick=()=>{const clone=$('plot').cloneNode(true);clone.setAttribute('xmlns',ns);const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(clone)],{type:'image/svg+xml'}));const a=document.createElement('a');a.href=url;a.download='chromaticity-'+data.profile+'.svg';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
update();
</script></body></html>"""
    document = (
        template.replace(
            "__TITLE__", "Диаграмма цветности" if ru else "Chromaticity explorer"
        )
        .replace("__LANG__", language)
        .replace(
            "__PAYLOAD__", json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
        )
    )
    path = config.artifacts / profile / f"chromaticity_{language}.html"
    path.write_text(document, encoding="utf-8")
    from IPython.display import display

    title = "Диаграмма цветности" if ru else "Chromaticity explorer"
    display(
        {
            "text/html": '<iframe title="'
            + title
            + '" style="width:100%;height:1160px;border:0" sandbox="allow-scripts allow-downloads" srcdoc="'
            + html.escape(document, quote=True)
            + '"></iframe>'
        },
        raw=True,
    )
