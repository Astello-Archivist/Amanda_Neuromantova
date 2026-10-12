"""Extract conservative entity tags from embedded lyrics, retaining evidence."""
import csv
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def normalize(text):
    text = text.casefold().replace('\u0301', '').replace('ё', 'е')
    text = text.translate(str.maketrans({'á':'а','é':'е','ó':'о','ú':'у','í':'и'}))
    return unicodedata.normalize('NFC', text)

ALIASES = {
    'Агонит': ['агонит', 'agonit'],
    'Галедар': ['галедар', 'galedar'],
    'Эдвархейд': ['эдвархейд', 'эдвардхейд', 'эдвард хейнд', 'эдвард хэйнд', 'эдвард хейд', 'edward hand', 'edward haynd', 'edvardheind'],
    'Нагвар': ['нагвар', 'nagvar', 'nagwar'],
    'Кисик': ['кисик', 'киссик', 'kissik'],
    'Морверон': ['морверон', 'morveron'],
    'Валенар': ['валенар', 'valenar'],
    'Борг': ['борг', 'borg'],
    'Аларак': ['аларак', 'alarak'],
    'Геннифер': ['геннифер', 'генни', 'genipher'],
    'Рыцарь жёлтых трусов': ['рыцарь желтых трусов', 'рыцарь в желтых трусах', 'желтотрусов', 'knight yellow pants'],
    'Фогвинд': ['фогвинд', 'fogwind'],
    'Кроу': ['кроу'],
    'Эрилин': ['эрилин', 'erilin'],
    'Рабас': ['рабас'],
    'Торта': ['торта'],
    'Ассуми': ['ассуми'],
    'Ривендер': ['ривендер', 'ривендэр', 'rivendare', 'rivendari'],
    'Исида': ['исида', 'isis', 'isidis'],
    'Кел’Тузад': ["кел'тузад", 'кел’тузад', 'келтузад'],
    'Нефариан': ['нефариан'],
    'Каззак': ['каззак'],
    'Пахом': ['пахом'],
    'Берджерджил': ['берджерджил'],
    'Тимерий': ['тимерий', 'тамерий'],
    'Дервиас': ['дервиас'],
    'Морнэ': ['морнэ'],
    'Сильмари': ['сильмари'],
    'Димачка': ['димачка'],
    'Артурчик': ['артурчик'],
    'КусокТора': ['кусоктора'],
    'Сковальд': ['сковальд'],
    'Харуша': ['харуша'],
    'Аларион': ['аларион'],
    'Чарльз Боулер': ['чарльз боулер'],
    'Дагл Бёрк': ['дагл берк'],
    'Карл': ['карл'],
    'Сьюзи': ['сьюзи'],
    'Авен': ['авен'],
    'Айвен': ['айвен'],
    'Виктор': ['виктор'],
    'Арчер': ['арчер'],
    'Светлана Баскова': ['светлана баскова'],
    'Шалавелла': ['шалавелла'],
    'Дулин': ['дулин'],
    'СоСори': ['сосори'],
    'Данко': ['данко'],
    'Миша': ['миша', 'мишан', 'мишенька', 'мишаня', 'мишанчик', 'мишка', 'михаил'],
    'Саша': ['саша', 'сашенька', 'сашуля'],
    'Денис': ['денис', 'дэнис', 'дэниз'],
    'Костя': ['костя', 'константин'],
    'Максим': ['максим'],
    'Андрей': ['андрей'],
}
ITEMS = {'Чёрный Алмаз': ['черный алмаз', 'black diamond'],
         'Коричневый Алмаз': ['коричневый алмаз'],
         'Алмаз из говнистых глубин': ['алмаз из говнистых глубин'],
         'Литтл Мерри': ['литтл мерри', 'little merry']}

def extract(text, dictionary):
    found = {}
    for name, aliases in dictionary.items():
        for alias in aliases:
            match = re.search(r'(?<!\w)' + re.escape(normalize(alias)) + r'(?!\w)', text)
            if match:
                found[name] = text[max(0, match.start()-65):match.end()+65]
                break
    return found

def main():
    with (ROOT/'tracks.csv').open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        fields = reader.fieldnames
        rows = list(reader)
    evidence = []
    for row in rows:
        if not row['lyrics'].strip():
            continue
        text = normalize(row['lyrics'])
        entities = extract(text, ALIASES)
        items = extract(text, ITEMS)
        for field, values in [('characters', entities), ('items', items)]:
            existing = [x.strip() for x in row[field].split('|') if x.strip()]
            row[field] = ' | '.join(dict.fromkeys(existing + list(values)))
        # Only lyrics with explicit descriptions of these named animals.
        animals = {'CHD-0032': ['Рабас', 'Торта'], 'CHD-0083': ['Кисик'],
                   'CHD-0085': ['Кисик']}.get(row['id'], [])
        if animals and not row['named_animals']:
            row['named_animals'] = ' | '.join(animals)
        evidence.append({'id': row['id'], 'source': 'embedded_lyrics',
                         'characters': entities, 'items': items, 'named_animals': animals})
    with (ROOT/'tracks.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    (ROOT/'tag_evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'lyrics_checked': len(evidence), 'tracks_with_characters': sum(bool(r['characters']) for r in rows), 'tracks_with_items': sum(bool(r['items']) for r in rows)}, ensure_ascii=True))

if __name__ == '__main__':
    main()
