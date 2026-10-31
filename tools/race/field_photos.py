#!/usr/bin/env python3
"""Car viewer data: public/cars/field/<track>/photos.json (Laguna: public/cars/field/photos.json).

Per car id, a list of {file, page_url} for every gallery photo in its kit folder that resolves through a SmugMug image
index, and {file, owner: true} for the owner's own photos (owner_*.jpg: no public URL). A photo resolves by file name
(without the _XL suffix and the extension) in the event's own index first; Laguna's other galleries (image_index_x_*)
and the other events' indexes are used only when the name is unique there. Never guesses a URL.

Run:  python3 -I tools/race/field_photos.py <kit field dir> <repo root>
  kit field dir = .../tools/cars/field (holds photos/ and smugmug/)
"""
import json, os, re, sys, glob

TRACKS = {  # track dir -> (identity path rel. to public/cars/field, photos dir rel. to the kit, own index)
    'laguna_seca': ('identity.json', 'photos', 'image_index.json', 'photos.json'),
    'sonoma': ('sonoma/identity.json', 'photos/sonoma', 'image_index_sonoma.json', 'sonoma/photos.json'),
    'buttonwillow': ('buttonwillow/identity.json', 'photos/buttonwillow', 'image_index_buttonwillow.json', 'buttonwillow/photos.json'),
    'mid_ohio': ('mid_ohio/identity.json', 'photos/mid_ohio', 'image_index_mid_ohio.json', 'mid_ohio/photos.json'),
}


def stem(name):
    s = os.path.splitext(name)[0]
    return s[:-3] if s.endswith('_XL') else s


def page_url(item):
    """https://24hoursoflemons.smugmug.com/Race/<gallery>/i-<key>, the gallery read from any size URL."""
    for u in item.get('sizes', {}).values():
        m = re.search(r'/Race/([^/]+)/i-' + re.escape(item['key']) + '/', u)
        if m:
            return f"https://24hoursoflemons.smugmug.com/Race/{m.group(1)}/i-{item['key']}"
    return None


def index_by_name(path):
    out = {}
    for it in json.load(open(path)):
        out.setdefault(it['file'], []).append(it)
    return out


def resolve(name, own, others):
    """Page URL or None. Own index first (a name repeated with different keys is ambiguous), then unique elsewhere."""
    for idx, strict in [(own, True)] + [(o, True) for o in others]:
        hits = idx.get(name, [])
        keys = {h['key'] for h in hits}
        if len(keys) == 1:
            u = page_url(hits[0])
            if u:
                return u
        if len(keys) > 1:
            return None
    return None


def pure_pick(name, own, others):
    # others: a name unique across all the other indexes together
    u = resolve(name, own, [])
    if u:
        return u
    seen = {}
    for o in others:
        for h in o.get(name, []):
            seen[h['key']] = h
    if len(seen) == 1:
        return page_url(next(iter(seen.values())))
    return None


def main(kit, repo):
    smug = os.path.join(kit, 'smugmug')
    allidx = {os.path.basename(p): index_by_name(p) for p in glob.glob(os.path.join(smug, 'image_index*.json'))}
    for track, (ident, pdir, own_name, out_rel) in TRACKS.items():
        identity = json.load(open(os.path.join(repo, 'public/cars/field', ident)))
        own = allidx[own_name]
        others = [v for k, v in allidx.items() if k != own_name]
        res, ok, bad, nown = {}, 0, [], 0
        for row in identity:
            cid = str(row.get('id') or row['number'])
            d = os.path.join(kit, row.get('photo_dir') or f"{pdir}/{cid}")
            if not os.path.isdir(d):
                continue
            seen, items = set(), []
            for f in sorted(os.listdir(d)):
                if not f.lower().endswith('.jpg'):
                    continue
                s = stem(f)
                if s in seen:
                    continue
                seen.add(s)
                if s.startswith('owner_'):
                    items.append({'file': s + '.jpg', 'owner': True}); nown += 1
                    continue
                u = pure_pick(s, own, others)
                if u:
                    items.append({'file': s + '.jpg', 'page_url': u}); ok += 1
                else:
                    bad.append(f'{cid}/{s}')
            if items:
                res[cid] = items
        with open(os.path.join(repo, 'public/cars/field', out_rel), 'w') as fh:
            json.dump(res, fh, indent=1, sort_keys=True); fh.write('\n')
        print(f'{track}: {len(res)} cars with photos, {ok} resolved, {nown} owner, {len(bad)} unresolved')
        for b in bad:
            print('  unresolved:', b)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
