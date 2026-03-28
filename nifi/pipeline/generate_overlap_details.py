from pathlib import Path
import json, re, sys
base=Path('../nifi/processors').resolve()
files={'bhs':base/'bhs_col_map.py','ehvol':base/'ehvol_col_map.py'}
colmaps={}
for k,f in files.items():
    if not f.exists():
        print('Missing', f, file=sys.stderr); sys.exit(1)
    g={}
    exec(f.read_text(), g)
    cm=g.get('COLUMN_MAP',{})
    colmaps[k]=[v[0] for v in cm.values()]
A=set(colmaps['bhs'])
B=set(colmaps['ehvol'])
inter=sorted(A&B)
onlyA=sorted(A-B)
onlyB=sorted(B-A)
out=Path('../outputs').resolve()
out.mkdir(parents=True, exist_ok=True)
(out/'intersection.csv').write_text('\n'.join(inter))
(out/'only_bhs.csv').write_text('\n'.join(onlyA))
(out/'only_ehvol.csv').write_text('\n'.join(onlyB))

def norm(s):
    s=s.lower()
    s=re.sub(r'[_\-\s]+','_',s)
    s=re.sub(r'(_in|_cm|_kg|_mm|_date|_d|_kg$|_cm$)|\b(cm|kg|mm|date|in|value|measurement|measurement_\d+)\b','',s)
    s=re.sub(r'[^a-z0-9_]','',s)
    s=re.sub(r'_+','_',s).strip('_')
    return s
onlyA_norm={c:norm(c) for c in onlyA}
onlyB_norm={c:norm(c) for c in onlyB}

def jaccard(a,b):
    sa=set(a.split('_'))
    sb=set(b.split('_'))
    if not sa or not sb: return 0.0
    return len(sa&sb)/len(sa|sb)

probable_matches=[]
for a,c1 in onlyA_norm.items():
    best=(None,0.0)
    for b,c2 in onlyB_norm.items():
        if not c1 or not c2: continue
        if c1==c2:
            best=(b,1.0); break
        score=jaccard(c1,c2)
        if c1 in c2 or c2 in c1:
            score=max(score,0.9)
        if score>best[1]: best=(b,score)
    if best[1]>=0.5:
        probable_matches.append({'bhs':a,'ehvol':best[0],'score':round(best[1],2)})

matched_bhs={p['bhs'] for p in probable_matches}
matched_ehvol={p['ehvol'] for p in probable_matches}
unmatched_bhs=[c for c in onlyA if c not in matched_bhs]
unmatched_ehvol=[c for c in onlyB if c not in matched_ehvol]

report={'counts':{'n_bhs':len(A),'n_ehvol':len(B),'n_both':len(inter),'n_only_bhs':len(onlyA),'n_only_ehvol':len(onlyB)},
        'n_probable_matches':len(probable_matches),
        'n_unmatched_bhs':len(unmatched_bhs),'n_unmatched_ehvol':len(unmatched_ehvol),
        'probable_matches_sample':probable_matches[:200],
        'example_unmatched_bhs':unmatched_bhs[:50],
        'example_unmatched_ehvol':unmatched_ehvol[:50]}

(out/'overlap_details.json').write_text(json.dumps(report,indent=2))
print('WROTE', out)
