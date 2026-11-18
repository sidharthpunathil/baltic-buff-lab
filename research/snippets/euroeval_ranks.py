import csv,re,sys
lang=sys.argv[1]; pat=re.compile(sys.argv[2],re.I) if len(sys.argv)>2 else None
rows=list(csv.reader(open(f'{lang}_all.csv')))
hdr=rows[1]; names=[re.sub('<[^>]*>','',h) for h in hdr]
out=[]
for r in rows[2:]:
    m=re.sub('<[^>]*>','',r[0])
    if pat and not pat.search(m): continue
    out.append(((lambda v: float(v) if v.replace(".","",1).isdigit() else 99)(r[2].split("@@")[0]),m,r[3],dict(zip(names[10:17],r[10:17]))))
out.sort()
print(lang, 'n_models=',len(rows)-2, 'tasks=',names[10:17])
for rank,m,p,sc in out[:int(sys.argv[3]) if len(sys.argv)>3 else 25]:
    print(f"{rank:5.2f} | {m[:70]:70} | {p:>6} | " + " ".join(v.split("@@")[0] for v in sc.values()))
