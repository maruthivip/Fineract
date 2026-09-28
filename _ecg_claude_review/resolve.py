import json,os,subprocess,collections
ROOT=os.path.abspath("..")
claims=json.load(open("claims.json"))
jf=[l.strip() for l in open(os.path.expanduser("~/idx/java_files.txt"))]
base=collections.defaultdict(list)
for p in jf: base[os.path.basename(p)[:-5]].append(p)
mods=set(l.strip() for l in open(os.path.expanduser("~/idx/modules.txt")))
allpaths=set(jf)
# gather tokens needing grep
need=set()
for c in claims.values():
    need.update(c['enum']); need.update(c['table'])
need={t for t in need if len(t)>3}
pf="/tmp/pat.txt"
open(pf,"w").write("\n".join(sorted(need)))
hits=set()
if need:
    r=subprocess.run(["grep","-rhoFf",pf,"--include=*.java","--include=*.sql","--include=*.xml","--include=*.json","."],cwd=ROOT,capture_output=True,text=True)
    hits=set(r.stdout.split())
out={}
for qid,c in claims.items():
    res={}
    res['cls']={t:(base[t][:2] if t in base else None) for t in c['cls']}
    res['module']={t:(t in mods) for t in c['module']}
    res['path']={}
    for t in c['path']:
        t2=t.lstrip('./')
        m=[p for p in allpaths if p.endswith(t2)] if '/' in t2 else base.get(t2[:-5],[])
        res['path'][t]=m[:2] if m else None
    res['fqcn']={}
    for t in c['fqcn']:
        cls=t.split('.')[-1]
        pkg='/'.join(t.split('.')[:-1])
        m=[p for p in base.get(cls,[]) if pkg in p]
        res['fqcn'][t]=m[:2] if m else (base.get(cls,[])[:2] or None)
    res['enum']={t:(t in hits) for t in c['enum']}
    res['table']={t:(t in hits) for t in c['table']}
    out[qid]=res
json.dump(out,open("resolved.json","w"),indent=0)
# summary of failures
bad=collections.defaultdict(list)
for qid,r in out.items():
    for k in ['cls','path','fqcn']:
        for t,v in r[k].items():
            if v is None: bad[qid].append(k+":"+t)
    for k in ['enum','table']:
        for t,v in r[k].items():
            if not v: bad[qid].append(k+":"+t)
    if not r['module'].get('x',True): pass
    for t,v in r['module'].items():
        if not v: bad[qid].append("module:"+t)
print("rows with unresolved:",len(bad),"/",len(out))
for q in sorted(bad): print(q,"|","; ".join(bad[q])[:400])
