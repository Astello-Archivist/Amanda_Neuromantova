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
const addedTime=r=>r.added_at&&Number.isFinite(Date.parse(r.added_at))?Date.parse(r.added_at):null;
const dayFormatter=new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Moscow',year:'numeric',month:'2-digit',day:'2-digit'});
const dateFormatter=new Intl.DateTimeFormat('ru-RU',{timeZone:'Europe/Moscow',day:'2-digit',month:'2-digit',year:'numeric'});
const addedDay=r=>addedTime(r)===null?'':dayFormatter.format(new Date(addedTime(r)));
const addedLabel=r=>addedTime(r)===null?'Не указана':dateFormatter.format(new Date(addedTime(r)));
function compareTracks(a,b){
 if(tableSort==='added_at'){
  const x=addedTime(a),y=addedTime(b);
  if(x===null||y===null)return x===y?0:x===null?1:-1;
  return tableDirection*(x-y||a.id.localeCompare(b.id));
 }
 const value=r=>tableSort==='title'?title(r):tableSort==='artist'?artist(r):tableSort==='duration'?Number(r.duration_seconds||0):tableSort==='genre'?genres(r).join(', '):r[tableSort]||'';
 return tableDirection*(tableSort==='duration'?value(a)-value(b):String(value(a)).localeCompare(String(value(b)),'ru'));
}
function inDateRange(r){const day=addedDay(r),from=$('addedFrom').value,to=$('addedTo').value;return (!from&&!to)||Boolean(day&&(!from||day>=from)&&(!to||day<=to));}
function applyPeriod(){
 const period=$('addedPeriod').value;
 if(period==='custom')return;
 $('addedFrom').value='';$('addedTo').value='';
 if(period){const today=dayFormatter.format(new Date()),start=new Date(today+'T00:00:00Z');start.setUTCDate(start.getUTCDate()-Number(period)+1);$('addedFrom').value=start.toISOString().slice(0,10);$('addedTo').value=today;}
 render();
}
const cultName=text=>String(text).replace(/(Ч[её]рн(?:ая|ой|ую|ою)\s+)длан(ь|и|ью)(?=$|[^а-яё])/gu,'$1Длан$2');
function el(tag,text,cls){const x=document.createElement(tag);if(text!==undefined)x.textContent=cultName(text);if(cls)x.className=cls;return x;}
function fill(id,values){[...new Set(values)].sort((a,b)=>a.localeCompare(b,'ru')).forEach(v=>{const o=el('option',v);o.value=v;$(id).append(o);});}
fill('artist',rows.map(artist));fill('genre',rows.flatMap(genres));fill('tag',rows.flatMap(tags));
const trackWord=n=>n%100>=11&&n%100<=14?'треков':n%10===1?'трек':n%10>=2&&n%10<=4?'трека':'треков';
const trackCount=el('div');trackCount.append(el('strong',rows.length),document.createTextNode(trackWord(rows.length)));$('stats').append(trackCount);
function artwork(r){const a=el('div',undefined,'art');const placeholder=()=>a.prepend(el('span','CH—D','fallback'));if(r.cover_path){const img=el('img');img.src=r.cover_path;img.alt='Обложка: '+title(r);img.loading='lazy';img.onerror=()=>{img.remove();placeholder();};a.append(img);}else placeholder();a.append(el('small',time(r.duration_seconds)));return a;}
function chips(r){const box=el('div',undefined,'tags');[...new Set([...genres(r),...tags(r)])].forEach(t=>box.append(el('span',t)));return box;}
function safeLink(url){try{const u=new URL(url);return ['https:','http:'].includes(u.protocol)?u.href:null;}catch{return null;}}
function show(r){const box=$('detailContent');box.replaceChildren(artwork(r),el('p',artist(r),'artist'),el('h2',title(r)),chips(r));const dl=el('dl');for(const [key,value] of [['Файл',r.file],['Длительность',time(r.duration_seconds)],['Добавлен в каталог',addedLabel(r)],['Жанр',genres(r).join(', ')||'Не указан'],['Персонажи',r.characters||'Пока не указаны'],['Предметы',r.items||'Пока не указаны'],['Животные',r.named_animals||'Пока не указаны'],['Альбом',r.metadata_album||'Не указан']])dl.append(el('dt',key),el('dd',value));box.append(dl);const links=el('div',undefined,'links');for(const [key,label] of [['audius_url','Audius ↗'],['drive_url','Google Drive ↗'],['youtube_url','YouTube ↗']]){const href=safeLink(r[key]);if(href){const a=el('a',label);a.href=href;a.target='_blank';a.rel='noopener noreferrer';links.append(a);}}box.append(links.children.length?links:el('p','Ссылки на прослушивание ещё не добавлены.','note'));if(r.notes)box.append(el('p',r.notes,'note'));if(r.lyrics)box.append(el('h3','Текст песни'),el('div',r.lyrics,'lyrics'));$('detail').showModal();}
function render(){
 const q=normalize($('search').value.trim()),invalid=Boolean($('addedFrom').value&&$('addedTo').value&&$('addedFrom').value>$('addedTo').value);
 $('dateError').hidden=!invalid;
 for(const id of ['addedFrom','addedTo'])$(id).setAttribute('aria-invalid',String(invalid));
 const visible=rows.filter(r=>!invalid&&inDateRange(r)&&(!q||normalize([r.file,title(r),artist(r),...genres(r),...tags(r),r.lyrics,r.notes].join(' ')).includes(q))&&(!$('artist').value||artist(r)===$('artist').value)&&(!$('genre').value||genres(r).includes($('genre').value))&&(!$('tag').value||tags(r).includes($('tag').value))&&(!$('cover').value||Boolean(r.cover_path)===($('cover').value==='yes')));
 visible.sort(compareTracks);
 $('count').textContent=`Показано ${visible.length} из ${rows.length} треков`;$('empty').hidden=visible.length>0||invalid;
 if(tableView){renderTable(visible);return;}
 const fragment=document.createDocumentFragment();visible.forEach(r=>{const card=el('button',undefined,'track');card.type='button';card.setAttribute('aria-label',`${title(r)} — ${artist(r)}. Подробнее`);const info=el('div',undefined,'info');info.append(el('p',artist(r),'artist'),el('h2',title(r)),el('p','Добавлен: '+addedLabel(r),'added-date'),chips(r));card.append(artwork(r),info);card.onclick=()=>show(r);fragment.append(card);});$('tracks').replaceChildren(fragment);
}
$('sort').addEventListener('change',()=>{const sort=$('sort').value;tableSort=sort==='newest'||sort==='oldest'?'added_at':sort;tableDirection=sort==='newest'||sort==='duration'?-1:1;});
$('addedPeriod').addEventListener('change',applyPeriod);
['addedFrom','addedTo'].forEach(id=>$(id).addEventListener('change',()=>{$('addedPeriod').value='custom';render();}));
['search','artist','genre','tag','cover','sort'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',render));
$('reset').onclick=()=>{['search','artist','genre','tag','cover','addedPeriod','addedFrom','addedTo'].forEach(id=>$(id).value='');$('sort').value='title';tableSort='title';tableDirection=1;render();};
$('view').onclick=()=>{tableView=!tableView;$('tracks').hidden=tableView;$('tableWrap').hidden=!tableView;$('view').textContent=tableView?'Показать карточки':'Показать таблицу';$('view').setAttribute('aria-pressed',String(!tableView));render();};

function renderTable(data){
 const table=el('table',undefined,'music-table');
 const caption=el('caption','Музыкальная коллекция — сортировка кнопками в заголовках');table.append(caption);
 const head=el('thead'),tr=el('tr');
 for(const [key,label] of [['cover','Обложка'],['title','Трек'],['artist','Исполнитель'],['characters','Персонажи'],['items','Предметы'],['named_animals','Животные'],['genre','Жанр'],['duration','Время'],['added_at','Добавлен'],['listen','Слушать']]){
  const th=el('th');th.scope='col';
  if(key==='cover'||key==='listen')th.textContent=label;
  else {const active=tableSort===key;th.setAttribute('aria-sort',active?(tableDirection===1?'ascending':'descending'):'none');const b=el('button',label+(active?(tableDirection===1?' ↑':' ↓'):''));b.type='button';b.onclick=()=>{tableDirection=active?-tableDirection:key==='added_at'?-1:1;tableSort=key;$('sort').value=key==='added_at'?(tableDirection===-1?'newest':'oldest'):['title','artist','duration'].includes(key)?key:'';render();};th.append(b);}
  tr.append(th);
 }
 head.append(tr);table.append(head);const body=el('tbody');
 for(const r of data){
  const row=el('tr');const art=el('td');art.append(artwork(r));row.append(art);
  const name=el('td');const b=el('button',title(r),'track-title');b.type='button';b.onclick=()=>show(r);name.append(b,el('small',r.id,'track-id'));row.append(name,el('td',artist(r)));
  for(const key of ['characters','items','named_animals']){const cell=el('td');const group=el('div',undefined,'tags');for(const tag of split(r[key])){const button=el('button',tag,'tag-filter');button.type='button';button.title='Фильтровать: '+tag;button.onclick=()=>{$('tag').value=tag;render();};group.append(button);}cell.append(group.children.length?group:document.createTextNode('—'));row.append(cell);}
  row.append(el('td',genres(r).join(', ')||'—'),el('td',time(r.duration_seconds),'duration'),el('td',addedLabel(r),'added-date'));
  const links=el('td');for(const [key,label] of [['audius_url','Audius ↗'],['youtube_url','YouTube ↗'],['drive_url','Drive ↗']]){const href=safeLink(r[key]);if(href){const a=el('a',label);a.href=href;a.target='_blank';a.rel='noopener noreferrer';links.append(a);}}
  if(!links.children.length)links.append(el('span','Скоро','unavailable'));row.append(links);body.append(row);
 }
 table.append(body);$('tableWrap').replaceChildren(table);
}

$('close').onclick=()=>$('detail').close();$('detail').addEventListener('click',e=>{if(e.target===$('detail')){const r=$('detail').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)$('detail').close();}});render();
