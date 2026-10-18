'use strict';
const rows=window.CATALOG_TRACKS||[];
let tableView=true, tableSort='title', tableDirection=1;
const $=id=>document.getElementById(id);
const split=value=>String(value||'').split('|').map(x=>x.trim()).filter(Boolean);
const artist=r=>r.artist_draft||r.metadata_artist||'Исполнитель не указан';
const title=r=>r.title_draft||r.metadata_title||r.file;
const genres=r=>split(r.genre||r.metadata_genre);
const tags=r=>['characters','items','named_animals'].flatMap(k=>split(r[k]));
const normalize=s=>String(s||'').toLocaleLowerCase('ru').replaceAll('ё','е');
const time=n=>Number(n)>0?`${Math.floor(n/60)}:${String(Math.floor(n%60)).padStart(2,'0')}`:'—';
const cultName=text=>String(text).replace(/(Ч[её]рн(?:ая|ой|ую|ою)\s+)длан(ь|и|ью)(?=$|[^а-яё])/gu,'$1Длан$2');
function el(tag,text,cls){const x=document.createElement(tag);if(text!==undefined)x.textContent=cultName(text);if(cls)x.className=cls;return x;}
function fill(id,values){[...new Set(values)].sort((a,b)=>a.localeCompare(b,'ru')).forEach(v=>{const o=el('option',v);o.value=v;$(id).append(o);});}
fill('artist',rows.map(artist));fill('genre',rows.flatMap(genres));fill('tag',rows.flatMap(tags));
const trackWord=n=>n%100>=11&&n%100<=14?'треков':n%10===1?'трек':n%10>=2&&n%10<=4?'трека':'треков';
const trackCount=el('div');trackCount.append(el('strong',rows.length),document.createTextNode(trackWord(rows.length)));$('stats').append(trackCount);
function artwork(r){const a=el('div',undefined,'art');const placeholder=()=>a.prepend(el('span','CH—D','fallback'));if(r.cover_path){const img=el('img');img.src=r.cover_path;img.alt='Обложка: '+title(r);img.loading='lazy';img.onerror=()=>{img.remove();placeholder();};a.append(img);}else placeholder();a.append(el('small',time(r.duration_seconds)));return a;}
function chips(r){const box=el('div',undefined,'tags');[...new Set([...genres(r),...tags(r)])].forEach(t=>box.append(el('span',t)));return box;}
function safeLink(url){try{const u=new URL(url);return ['https:','http:'].includes(u.protocol)?u.href:null;}catch{return null;}}
function show(r){const box=$('detailContent');box.replaceChildren(artwork(r),el('p',artist(r),'artist'),el('h2',title(r)),chips(r));const dl=el('dl');for(const [key,value] of [['Файл',r.file],['Длительность',time(r.duration_seconds)],['Жанр',genres(r).join(', ')||'Не указан'],['Персонажи',r.characters||'Пока не указаны'],['Предметы',r.items||'Пока не указаны'],['Животные',r.named_animals||'Пока не указаны'],['Альбом',r.metadata_album||'Не указан']])dl.append(el('dt',key),el('dd',value));box.append(dl);const links=el('div',undefined,'links');for(const [key,label] of [['audius_url','Audius ↗'],['drive_url','Google Drive ↗'],['youtube_url','YouTube ↗']]){const href=safeLink(r[key]);if(href){const a=el('a',label);a.href=href;a.target='_blank';a.rel='noopener noreferrer';links.append(a);}}box.append(links.children.length?links:el('p','Ссылки на прослушивание ещё не добавлены.','note'));if(r.notes)box.append(el('p',r.notes,'note'));if(r.lyrics)box.append(el('h3','Текст песни'),el('div',r.lyrics,'lyrics'));$('detail').showModal();}
function render(){const q=normalize($('search').value.trim());const visible=rows.filter(r=>(!q||normalize([r.file,title(r),artist(r),...genres(r),...tags(r),r.lyrics,r.notes].join(' ')).includes(q))&&(!$('artist').value||artist(r)===$('artist').value)&&(!$('genre').value||genres(r).includes($('genre').value))&&(!$('tag').value||tags(r).includes($('tag').value))&&(!$('cover').value||Boolean(r.cover_path)===($('cover').value==='yes')));visible.sort((a,b)=>$('sort').value==='duration'?Number(b.duration_seconds||0)-Number(a.duration_seconds||0):($('sort').value==='artist'?artist(a):title(a)).localeCompare($('sort').value==='artist'?artist(b):title(b),'ru'));$('count').textContent=`Показано ${visible.length} из ${rows.length} треков`;$('empty').hidden=visible.length>0;if(tableView){renderTable(visible);return;}const fragment=document.createDocumentFragment();visible.forEach(r=>{const card=el('button',undefined,'track');card.type='button';card.setAttribute('aria-label',`${title(r)} — ${artist(r)}. Подробнее`);const info=el('div',undefined,'info');info.append(el('p',artist(r),'artist'),el('h2',title(r)),chips(r));card.append(artwork(r),info);card.onclick=()=>show(r);fragment.append(card);});$('tracks').replaceChildren(fragment);}
$('sort').addEventListener('change',()=>{tableSort=$('sort').value;tableDirection=tableSort==='duration'?-1:1;});
['search','artist','genre','tag','cover','sort'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',render));
$('reset').onclick=()=>{['search','artist','genre','tag','cover'].forEach(id=>$(id).value='');$('sort').value='title';tableSort='title';tableDirection=1;render();};
$('view').onclick=()=>{tableView=!tableView;$('tracks').hidden=tableView;$('tableWrap').hidden=!tableView;$('view').textContent=tableView?'Показать карточки':'Показать таблицу';$('view').setAttribute('aria-pressed',String(!tableView));render();};

function renderTable(data){
 const value=(r,k)=>k==='title'?title(r):k==='artist'?artist(r):k==='duration'?Number(r.duration_seconds||0):k==='genre'?genres(r).join(', '):r[k]||'';
 data.sort((a,b)=>tableDirection*(tableSort==='duration'?value(a,tableSort)-value(b,tableSort):String(value(a,tableSort)).localeCompare(String(value(b,tableSort)),'ru')));
 const table=el('table',undefined,'music-table');
 const caption=el('caption','Музыкальная коллекция — сортировка кнопками в заголовках');table.append(caption);
 const head=el('thead'),tr=el('tr');
 for(const [key,label] of [['cover','Обложка'],['title','Трек'],['artist','Исполнитель'],['characters','Персонажи'],['items','Предметы'],['named_animals','Животные'],['genre','Жанр'],['duration','Время'],['listen','Слушать']]){
  const th=el('th');th.scope='col';
  if(key==='cover'||key==='listen')th.textContent=label;
  else {const active=tableSort===key;th.setAttribute('aria-sort',active?(tableDirection===1?'ascending':'descending'):'none');const b=el('button',label+(active?(tableDirection===1?' ↑':' ↓'):''));b.type='button';b.onclick=()=>{tableDirection=active?-tableDirection:1;tableSort=key;render();};th.append(b);}
  tr.append(th);
 }
 head.append(tr);table.append(head);const body=el('tbody');
 for(const r of data){
  const row=el('tr');const art=el('td');art.append(artwork(r));row.append(art);
  const name=el('td');const b=el('button',title(r),'track-title');b.type='button';b.onclick=()=>show(r);name.append(b,el('small',r.id,'track-id'));row.append(name,el('td',artist(r)));
  for(const key of ['characters','items','named_animals']){const cell=el('td');const group=el('div',undefined,'tags');for(const tag of split(r[key])){const button=el('button',tag,'tag-filter');button.type='button';button.title='Фильтровать: '+tag;button.onclick=()=>{$('tag').value=tag;render();};group.append(button);}cell.append(group.children.length?group:document.createTextNode('—'));row.append(cell);}
  row.append(el('td',genres(r).join(', ')||'—'),el('td',time(r.duration_seconds),'duration'));
  const links=el('td');for(const [key,label] of [['audius_url','Audius ↗'],['youtube_url','YouTube ↗'],['drive_url','Drive ↗']]){const href=safeLink(r[key]);if(href){const a=el('a',label);a.href=href;a.target='_blank';a.rel='noopener noreferrer';links.append(a);}}
  if(!links.children.length)links.append(el('span','Скоро','unavailable'));row.append(links);body.append(row);
 }
 table.append(body);$('tableWrap').replaceChildren(table);
}

$('close').onclick=()=>$('detail').close();$('detail').addEventListener('click',e=>{if(e.target===$('detail')){const r=$('detail').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)$('detail').close();}});render();
