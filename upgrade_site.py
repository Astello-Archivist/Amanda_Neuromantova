"""One-time migration adding an accessible sortable table view."""
from pathlib import Path
p = Path(__file__).resolve().parent
html = (p/'music.html').read_text(encoding='utf-8')
html = html.replace('<a class="download" href="tracks.csv" download>Скачать таблицу ↗</a>', '<a class="download" href="Ch-D_music_catalog.xlsx" download>Скачать Excel ↗</a>')
html = html.replace('Вид: карточки', 'Показать карточки')
html = html.replace('<div id="tracks" class="grid"></div>', '<div id="tracks" class="grid" hidden></div><div id="tableWrap" class="table-wrap"></div>')
html = html.replace('Коллекция пополняется. Теги и ссылки появятся по мере заполнения таблицы.', 'Поиск по названиям, тегам и текстам. Нажмите на название песни, чтобы открыть подробности.')
(p/'music.html').write_text(html, encoding='utf-8')
js = (p/'catalog.js').read_text(encoding='utf-8')
js = js.replace("const rows=window.CATALOG_TRACKS||[];", "const rows=window.CATALOG_TRACKS||[];\nlet tableView=true, tableSort='title', tableDirection=1;")
js = js.replace("const fragment=document.createDocumentFragment();visible.forEach", "if(tableView){renderTable(visible);return;}const fragment=document.createDocumentFragment();visible.forEach")
start = js.index("$('view').onclick=")
end = js.index("$('close').onclick=", start)
js = js[:start] + "$('view').onclick=()=>{tableView=!tableView;$('tracks').hidden=tableView;$('tableWrap').hidden=!tableView;$('view').textContent=tableView?'Показать карточки':'Показать таблицу';$('view').setAttribute('aria-pressed',String(!tableView));render();};\n" + js[end:]
js = js.replace("['search','artist','genre','tag','cover','sort'].forEach", "$('sort').addEventListener('change',()=>{tableSort=$('sort').value;tableDirection=tableSort==='duration'?-1:1;});\n['search','artist','genre','tag','cover','sort'].forEach")
js = js.replace("$('sort').value='title';render();", "$('sort').value='title';tableSort='title';tableDirection=1;render();")
helper = '''
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
  const links=el('td');for(const [key,label] of [['youtube_url','YouTube ↗'],['drive_url','Drive ↗']]){const href=safeLink(r[key]);if(href){const a=el('a',label);a.href=href;a.target='_blank';a.rel='noopener noreferrer';links.append(a);}}
  if(!links.children.length)links.append(el('span','Скоро','unavailable'));row.append(links);body.append(row);
 }
 table.append(body);$('tableWrap').replaceChildren(table);
}
'''
js = js.replace("$('close').onclick=",helper+"\n$('close').onclick=")
(p/'catalog.js').write_text(js, encoding='utf-8')
css = '''
[hidden]{display:none!important}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel)}.music-table{width:100%;border-collapse:collapse;font-size:13px;min-width:1100px}.music-table caption{text-align:left;padding:16px;color:var(--muted);font-size:12px}.music-table th{background:#26342a;text-align:left;white-space:nowrap;padding:10px;position:sticky;top:0;z-index:1}.music-table th button{border:0;background:transparent;padding:4px;color:var(--accent);font-size:12px}.music-table td{padding:12px 10px;border-top:1px solid var(--line);vertical-align:middle}.music-table tbody tr:nth-child(even){background:#ffffff04}.music-table tbody tr:hover{background:#d3ed9b0a}.music-table .art{width:56px;height:56px}.music-table .art small{display:none}.music-table .fallback{font-size:16px}.track-title{border:0;padding:0;background:transparent;text-align:left;min-width:180px;font-weight:600}.track-title:hover{text-decoration:underline}.track-id{display:block;color:var(--muted);font-size:10px;margin-top:5px}.music-table .tags{margin:0;min-width:100px}.tag-filter{font-size:10px;padding:3px 7px;border-radius:16px;color:var(--accent);border-color:#455039;background:transparent}.duration{white-space:nowrap;font-variant-numeric:tabular-nums}.unavailable{color:var(--muted);font-size:11px}.music-table td>a{display:block;white-space:nowrap;color:var(--accent);margin:4px 0}
'''
with (p/'catalog.css').open('a',encoding='utf-8') as f:f.write(css)
