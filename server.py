from flask import Flask, request, jsonify, send_from_directory
import json, os, time
app = Flask(__name__)
if not os.path.exists('db.json'):
    json.dump({"msgs": {}, "perfis": {}, "users": {"izac": "e6s123"}, "codes": {}, "premium": ["izac"], "aviso": "", "avatars": {}, "dms": {}}, open('db.json','w'))
def load(): return json.load(open('db.json'))
def save(d): json.dump(d, open('db.json','w'))
d0=load()
for k,v in [("msgs",{}),("perfis",{}),("codes",{}),("avatars",{}),("dms",{}),("premium",["izac"]),("aviso","")]:
    if k not in d0: d0[k]=v
if "izac" not in d0["users"]: d0["users"]["izac"]="e6s123"
if "izac" not in d0["premium"]: d0["premium"].append("izac")
save(d0)

@app.route('/')
def home(): return send_from_directory('.', 'login.html')
@app.route('/<path:p>')
def files(p): return send_from_directory('.', p)

@app.route('/api/register', methods=['POST'])
def register():
    d=load(); j=request.json; u=j.get('user','').lower().strip(); p=j.get('pass','').strip()
    if not u or not p: return jsonify({"ok":False,"msg":"Preenche tudo!"})
    if u in d["users"]: return jsonify({"ok":False,"msg":"Usuário já existe!"})
    d["users"][u]=p; save(d); return jsonify({"ok":True})
@app.route('/api/login', methods=['POST'])
def login():
    d=load(); j=request.json; u=j.get('user','').lower().strip(); p=j.get('pass','').strip()
    if d["users"].get(u)==p: return jsonify({"ok":True, "premium": u in d["premium"]})
    return jsonify({"ok":False,"msg":"Usuário ou senha errados!"})
@app.route('/api/users')
def users():
    d=load(); me=request.args.get('me','')
    return jsonify([u for u in d["users"].keys() if u!=me])
@app.route('/api/msgs')
def msgs():
    d=load(); ch=request.args.get('ch','geral'); return jsonify(d["msgs"].get(ch, [])[-60:])
@app.route('/api/send', methods=['POST'])
def send():
    d=load(); j=request.json; ch=j.get('ch','geral')
    if ch=='premium' and j["nome"] not in d["premium"]: return jsonify({"ok":False,"msg":"Só Premium!"})
    d["msgs"].setdefault(ch, []).append({"nome":j["nome"],"texto":j.get("texto",""),"cor":j.get("cor","#008a5c"),"avatar":j.get("avatar","🐠"),"tipo":j.get("tipo","texto"),"img":j.get("img",""),"premium": j["nome"] in d["premium"]})
    save(d); return jsonify({"ok":True})

def dm_key(a,b): return "__".join(sorted([a.lower(), b.lower()]))
@app.route('/api/dm')
def get_dm():
    d=load(); a=request.args.get('a',''); b=request.args.get('b','')
    return jsonify(d["dms"].get(dm_key(a,b), [])[-60:])
@app.route('/api/dm/send', methods=['POST'])
def send_dm():
    d=load(); j=request.json; a=j["de"]; b=j["para"]; k=dm_key(a,b)
    d["dms"].setdefault(k, []).append({"nome":a,"texto":j.get("texto",""),"cor":j.get("cor","#008a5c"),"avatar":j.get("avatar","🐠"),"tipo":j.get("tipo","texto"),"img":j.get("img",""),"premium": a in d["premium"]})
    save(d); return jsonify({"ok":True})

@app.route('/api/perfil', methods=['GET','POST'])
def perfil():
    d=load()
    if request.method=='POST':
        j=request.json; d["perfis"][j["user"]]=j; save(d); return jsonify({"ok":True})
    return jsonify(d["perfis"].get(request.args.get('user',''), {"cor":"#008a5c","avatar":"🐠","bio":"","premium": request.args.get('user','') in d["premium"]}))

@app.route('/api/adm', methods=['GET','POST'])
def adm():
    d=load(); j=request.json if request.method=='POST' else {}
    if j.get('adm')!='izac': return jsonify({"ok":False,"msg":"Só o ADM!"})
    acao=j.get('acao')
    if acao=='criar_codigo':
        # NOVO: tempo em minutos e max_uses
        minutos=int(j.get('minutos', 60))
        max_uses=int(j.get('max_uses', 1))
        d["codes"][j["codigo"]]={"tipo":j["tipo"],"valor":j["valor"],"expira": time.time() + minutos*60 if minutos>0 else 0, "max_uses": max_uses, "usos": 0}
        save(d); return jsonify({"ok":True})
    if acao=='aviso': d["aviso"]=j["texto"]; save(d); return jsonify({"ok":True})
    if acao=='dar_premium':
        if j["user"] not in d["premium"]: d["premium"].append(j["user"])
        save(d); return jsonify({"ok":True})
    if acao=='tirar_premium':
        if j["user"] in d["premium"]: d["premium"].remove(j["user"])
        save(d); return jsonify({"ok":True})
    return jsonify(d)

@app.route('/api/resgatar', methods=['POST'])
def resgatar():
    d=load(); j=request.json; cod=j.get('codigo','').upper(); u=j.get('user')
    if cod not in d["codes"]: return jsonify({"ok":False,"msg":"Código inválido ou já acabou!"})
    c=d["codes"][cod]
    # checa tempo
    if c.get("expira",0)>0 and time.time() > c["expira"]:
        del d["codes"][cod]; save(d); return jsonify({"ok":False,"msg":"Código expirou!"})
    # checa limite
    if c.get("usos",0) >= c.get("max_uses",1):
        del d["codes"][cod]; save(d); return jsonify({"ok":False,"msg":"Código já atingiu o limite!"})
    # já resgatou antes?
    if c["tipo"]=="premium" and u in d["premium"]: return jsonify({"ok":False,"msg":"Tu já é Premium!"})
    if c["tipo"]=="avatar" and c["valor"] in d["avatars"].get(u,[]): return jsonify({"ok":False,"msg":"Tu já tem esse avatar!"})
    # aplica
    if c["tipo"]=="premium":
        if u not in d["premium"]: d["premium"].append(u)
    if c["tipo"]=="avatar":
        d["avatars"].setdefault(u, []).append(c["valor"])
    c["usos"] = c.get("usos",0)+1
    if c["usos"] >= c.get("max_uses",1):
        del d["codes"][cod]
    else:
        d["codes"][cod]=c
    save(d); return jsonify({"ok":True,"msg":f"Resgatado! {c['tipo']}: {c['valor']} ({c['usos']}/{c['max_uses']} usos)"})

@app.route('/api/info')
def info():
    d=load(); u=request.args.get('user','')
    return jsonify({"aviso":d.get("aviso",""),"premium": u in d["premium"],"meus_avatars": d["avatars"].get(u,[]),"is_adm": u=="izac"})

if __name__=='__main__': app.run(host='0.0.0.0', port=int(__import__('os').environ.get('PORT', 8000)))
