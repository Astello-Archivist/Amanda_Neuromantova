"""Append local recordings, preserving existing IDs, links, and editorial tags."""
import argparse,csv,hashlib,io,json,re
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import mutagen
from PIL import Image
from match_audius import catalog_names,normalized,DURATION_TOLERANCE

ROOT=Path(__file__).resolve().parent
SOURCE=Path(r'D:\досуг\Ch-D_music_collection')
INCOMING=SOURCE/'не сопоставлено'

EDITS={
 'Артас - это тебе не Лордерон.mp3':{
  'genre':'Мрачная электроника | Рэп','language':'Русский',
  'characters':['Артас','Борг','Аларак','Эдвархейд','Морверон','Генифер'],
  'summary':'Артас предостерегает Борга, Аларака и Эдвархейда от посещения Златоземья: рассказывает об ограблениях, потере глаза Морвероном и падении жрицы Генифер. Эд и Эдвархэйд объединены в этой записи, поскольку текст сам использует обе формы обращения к одному слушателю.',
  'items':[]},
 'Le Fondateur (Коричневая Длань).mp3':{
  'genre':'Джаз-рэп | Бум-бэп','language':'Русский | Французский',
  'characters':['Агонит','Кисик','Морверон','Миша','Дерьмодемон','Туртлашка'],
  'summary':'Агонит рассказывает об основании Черной Длани, строительстве в Valheim и превращает шутку с углём в образ «Коричневой Длани».',
  'items':[]},
 'Борг - Фарта больше нет.mp3':{
  'genre':'Мрачная электроника','language':'Русский',
  'characters':['Борг','Амани','Кисик','Кит’икс','Леадрин'],
  'summary':'Борг проигрывает имущество и тотем; история связывает Амани, превращение Кисик в Кит’икса и Леадрин. Амани не объединена с эльфийским аптекарем Имаани из отчётов.',
  'items':['Тотем Борга']},
 'Тотем Убежал.mp3':{
  'genre':'Латин-трэп | Реггетон | Рэп-метал','language':'Русский',
  'characters':['Борг','Кисик','Миша','Агонит','Эдвархейд','Аларак','Морверон','Фогвинд','Валенар'],
  'summary':'Компания ждёт входа на сервер и ловит оживший тотем Борга. Упоминаются прежние образы Фогвинд и Валенар.',
  'items':['Тотем Борга','Чёрный Алмаз']},
 "Фулгрим Великий Нос (Dragon's Dogma).mp3":{
  'genre':'Дип-хаус | Фанк-хаус','language':'Русский',
  'characters':['Фулгрим','Эд','Глиндра','Мирддин'],
  'summary':'В Вернворте Фулгрим насмехается над нищим Мирддином и получает проклятие. Эд сохранён под именем из песни; тождество с Эдвархейдом не утверждается.',
  'items':[]},
}
ALIASES={'Кисик':['Киссик','Кисик'],'Эдвархейд':['Эдвархэйд','Эдвархейд','Эдвард Хейнд','Эдвард'],
         'Кит’икс':["Кит'икс"],'Туртлашка':['Туртлашки'],'Чёрный Алмаз':['Чёрного Алмаза'],
         'Тотем Борга':['тотем']}

def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def tag(tags,key):return ' | '.join(str(x) for f in tags.getall(key) for x in getattr(f,'text',[]))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--audit-name',default='new-tracks-20261018')
    args=parser.parse_args()
    assert Path(args.audit_name).name==args.audit_name
    AUDIT=ROOT/'audius-import'/args.audit_name
    AUDIT.mkdir(exist_ok=True)
    with (ROOT/'tracks.csv').open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f,delimiter=';');fields=reader.fieldnames;rows=list(reader)
    if 'added_at' not in fields:fields.append('added_at')
    imported_at=datetime.now(ZoneInfo('Europe/Moscow')).isoformat()
    if not (AUDIT/'tracks-before.csv').exists():(AUDIT/'tracks-before.csv').write_bytes((ROOT/'tracks.csv').read_bytes())
    snapshot=json.loads((ROOT/'audius-import/astello-tracks.json').read_text('utf-8'))
    covers=json.loads((ROOT/'covers.json').read_text('utf-8'))
    metadata=json.loads((ROOT/'metadata.json').read_text('utf-8-sig'))
    existing_hashes={r['sha256']:r for r in rows}
    number=max(int(r['id'].split('-')[1]) for r in rows)+1
    evidence=json.loads((ROOT/'tag_evidence.json').read_text('utf-8'))
    changes=[];skipped=[]
    for file in sorted(INCOMING.iterdir(),key=lambda f:f.name.casefold()):
        if file.suffix.lower()!='.mp3':continue
        digest=hashlib.sha256(file.read_bytes()).hexdigest()
        if digest in existing_hashes:
            skipped.append({'file':file.name,'existing_id':existing_hashes[digest]['id']});continue
        audio=mutagen.File(file);tags=audio.tags
        row={key:'' for key in fields};row['id']=f'CHD-{number:04}';row['added_at']=imported_at;number+=1
        title=tag(tags,'TIT2') or file.stem
        artist,display_title=title.split(' - ',1) if ' - ' in title else (tag(tags,'TPE1'),title)
        lyrics='\n\n'.join(frame.text for frame in tags.getall('USLT'))
        row.update(file=file.name,relative_path=file.relative_to(SOURCE).as_posix(),artist_draft=artist,title_draft=display_title,
                   size_bytes=str(file.stat().st_size),sha256=digest,metadata_title=title,metadata_artist=tag(tags,'TPE1'),
                   metadata_album=tag(tags,'TALB'),metadata_genre=tag(tags,'TCON'),metadata_year=tag(tags,'TDRC'),
                   metadata_comment=' | '.join(str(f) for f in tags.getall('COMM')),duration_seconds=str(round(audio.info.length,6)),
                   bitrate_kbps=str(round(audio.info.bitrate/1000)),lyrics=lyrics)
        draft=EDITS[file.name]
        row.update(genre=draft['genre'],language=draft['language'],characters=' | '.join(draft['characters']),items=' | '.join(draft['items']))
        row['notes']=draft['summary']+' Текст и обложка извлечены из файла. Стиль указан по авторским музыкальным пометкам в тексте; отдельный анализ звучания не проводился.'
        proof={}
        for name in draft['characters']+draft['items']:
            match=next((m for alias in ALIASES.get(name,[name]) if (m:=re.search(re.escape(alias),lyrics,re.I))),None)
            assert match,(file.name,name)
            proof[name]=lyrics[max(0,match.start()-65):min(len(lyrics),match.end()+95)]
        # Lyrics describe people and a magical object, without a named animal.
        row['named_animals']=''
        images=sorted(tags.getall('APIC'),key=lambda p:int(p.type)!=3)
        paths=[]
        for n,picture in enumerate(images,1):
            with Image.open(io.BytesIO(picture.data)) as image:
                extension={'JPEG':'jpg','PNG':'png','WEBP':'webp'}.get(image.format)
                assert extension,image.format
                image.verify()
            relative=f'covers/{row["id"]}-{n}.{extension}'
            (ROOT/relative).write_bytes(picture.data);paths.append(relative)
            covers['images'].append({'track_id':row['id'],'path':relative,'picture_type':int(picture.type),'mime':picture.mime,'sha256':hashlib.sha256(picture.data).hexdigest()})
        row.update(cover_path=paths[0] if paths else '',cover_count=str(len(paths)),cover_paths=' | '.join(paths))
        candidates=[t for t in snapshot['data'] if catalog_names(row)&{normalized(t.get(k)) for k in ['title','orig_filename']} and t.get('is_available') and abs(audio.info.length-t['duration'])<=DURATION_TOLERANCE]
        assert len(candidates)==1,(file.name,[(t['title'],t['duration']) for t in candidates])
        remote=candidates[0];row['audius_url']='https://audius.co'+remote['permalink']
        assert remote['user']['handle'].lower()=='astello'
        rows.append(row);existing_hashes[digest]=row
        evidence.append({'id':row['id'],'source':'embedded_lyrics_reviewed','characters':{n:proof[n] for n in draft['characters']},'items':{n:proof[n] for n in draft['items']},'named_animals':[]})
        metadata.append({'relative_path':row['relative_path'],'System.Title':title,'System.Music.Artist':[row['metadata_artist']],
                         'System.Music.AlbumTitle':row['metadata_album'],'System.Media.Duration':round(audio.info.length*10000000),
                         'System.Audio.EncodingBitrate':audio.info.bitrate,'System.Audio.SampleRate':audio.info.sample_rate,
                         'System.Audio.ChannelCount':audio.info.channels,'System.Music.Lyrics':lyrics,'extractor':'mutagen'})
        changes.append({'id':row['id'],'file':file.name,'sha256':digest,'added_at':row['added_at'],'duration_seconds':audio.info.length,'audius_seconds':remote['duration'],
                        'delta_seconds':round(abs(audio.info.length-remote['duration']),6),'audius_url':row['audius_url'],'covers':paths,'tags':proof})
    # Resolve local paths after the owner reorganized the source folders.
    by_name=defaultdict(list)
    for file in SOURCE.rglob('*'):
        if file.is_file() and file.suffix.lower() in {'.mp3','.m4a','.flac','.wav'}:by_name[file.name].append(file)
    path_changes=[];missing=[]
    for row in rows:
        current=SOURCE/row['relative_path']
        if current.exists():continue
        candidates=[p for p in by_name[row['file']] if hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']]
        if len(candidates)==1:
            new=candidates[0].relative_to(SOURCE).as_posix();path_changes.append({'id':row['id'],'old':row['relative_path'],'new':new});row['relative_path']=new
        else:missing.append({'id':row['id'],'file':row['file']})
    with (ROOT/'tracks.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,delimiter=';');writer.writeheader();writer.writerows(rows)
    dump(ROOT/'covers.json',covers);dump(ROOT/'metadata.json',metadata);dump(ROOT/'tag_evidence.json',evidence)
    report={'checked_at':datetime.now(ZoneInfo('Europe/Moscow')).isoformat(),'catalog_tracks':len(rows),'added':changes,'skipped_duplicates':skipped,'local_path_updates':path_changes,'missing_local_sources':missing}
    dump(AUDIT/'report.json',report)
    print(json.dumps({'total':len(rows),'added':[{'id':x['id'],'file':x['file'],'audius_url':x['audius_url'],'delta_seconds':x['delta_seconds']} for x in changes],
                      'paths_updated':len(path_changes),'missing_sources':missing,'duplicate_files_skipped':skipped},ensure_ascii=False))

if __name__=='__main__':main()
