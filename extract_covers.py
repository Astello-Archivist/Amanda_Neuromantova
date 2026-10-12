from pathlib import Path
import csv,json,struct,hashlib
ROOT=Path(__file__).resolve().parent
SOURCE=next(Path('D:/').glob('*/Ch-D_music_collection'))
def sync(b):
 return sum(v << (7*(3-i)) for i,v in enumerate(b))
def pictures_mp3(p):
 with p.open('rb') as f:
  h=f.read(10)
  if h[:3]!=b'ID3': return []
  version=h[3]; data=f.read(sync(h[6:10]))
 if version not in (2,3,4): raise ValueError('Unsupported ID3 version')
 if version<4 and h[5]&128: data=data.replace(b'\xff\x00',b'\xff')
 pos=0; found=[]
 if h[5]&64 and version in (3,4): pos=(int.from_bytes(data[:4],'big')+4) if version==3 else sync(data[:4])
 while pos+(6 if version==2 else 10)<=len(data):
  n=6 if version==2 else 10; frame=data[pos:pos+n]; name=frame[:3 if version==2 else 4]
  if not name.strip(b'\0'): break
  size=int.from_bytes(frame[3:6],'big') if version==2 else (sync(frame[4:8]) if version==4 else int.from_bytes(frame[4:8],'big'))
  body=data[pos+n:pos+n+size];pos+=n+size
  if size<=0: break
  if name not in (b'APIC',b'PIC'): continue
  if version==4 and frame[9]&2: body=body.replace(b'\xff\x00',b'\xff')
  if not body: continue
  enc=body[0]
  if version==2: mime={b'JPG':'image/jpeg',b'PNG':'image/png'}.get(body[1:4],''); k=4
  else:
   end=body.find(b'\0',1)
   if end<0: continue
   mime=body[1:end].decode('latin1');k=end+1
  if k>=len(body): continue
  kind=body[k];k+=1
  if enc in (1,2):
   while k+1<len(body) and body[k:k+2]!=b'\0\0': k+=2
   k+=2
  else:
   end=body.find(b'\0',k)
   if end<0: continue
   k=end+1
  if mime!='--> ' and mime!='-->': found.append((body[k:],kind,mime))
 return found
def pictures_mp4(p):
 data=p.read_bytes();found=[]
 def walk(start,end):
  while start+8<=end:
   size=int.from_bytes(data[start:start+4],'big');tag=data[start+4:start+8];header=8
   if size==1:
    size=int.from_bytes(data[start+8:start+16],'big');header=16
   elif size==0: size=end-start
   if size<header or start+size>end: break
   a=start+header;b=start+size
   if tag in (b'moov',b'udta',b'ilst'): walk(a,b)
   elif tag==b'meta': walk(a+4,b)
   elif tag==b'covr':
    cursor=a
    while cursor+16<=b:
     length=int.from_bytes(data[cursor:cursor+4],'big')
     if length<16 or cursor+length>b: break
     if data[cursor+4:cursor+8]==b'data': found.append((data[cursor+16:cursor+length],3,''))
     cursor+=length
   start+=size
 walk(0,len(data));return found
def extension(blob):
 if blob.startswith(b'\xff\xd8\xff'): return '.jpg'
 if blob.startswith(b'\x89PNG\r\n\x1a\n'): return '.png'
 if blob.startswith((b'GIF87a',b'GIF89a')): return '.gif'
 if blob[:4]==b'RIFF' and blob[8:12]==b'WEBP': return '.webp'
 return '.bin'
def main():
 with (ROOT/'tracks.csv').open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f,delimiter=';'))
 out=ROOT/'covers';out.mkdir(exist_ok=True);manifest=[];errors=[]
 for r in rows:
  p=SOURCE/r['relative_path'];images=[]
  try: images=pictures_mp3(p) if p.suffix.lower()=='.mp3' else pictures_mp4(p)
  except Exception as e: errors.append({'file':r['file'],'error':str(e)})
  paths=[];primary=''
  for index,(blob,kind,mime) in enumerate(images,1):
   if not blob: continue
   name=f"{r['id']}-{index}{extension(blob)}";target=out/name;target.write_bytes(blob)
   relative='covers/'+name;paths.append(relative)
   if not primary or kind==3: primary=relative
   manifest.append({'track_id':r['id'],'path':relative,'picture_type':kind,'mime':mime,'sha256':hashlib.sha256(blob).hexdigest()})
  r['cover_path']=primary;r['cover_count']=len(paths);r['cover_paths']=' | '.join(paths)
 with (ROOT/'tracks.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';');w.writeheader();w.writerows(rows)
 (ROOT/'tracks.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
 (ROOT/'covers.json').write_text(json.dumps({'images':manifest,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'tracks_with_covers':sum(bool(r['cover_path']) for r in rows),'images':len(manifest),'errors':errors}))
 assert all((ROOT/m['path']).is_file() for m in manifest)
if __name__=='__main__': main()
