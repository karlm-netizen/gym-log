# -*- coding: utf-8 -*-
"""Wegwerf-Sonde des Agentenlaufs. Wird nach dem Lauf geloescht."""
import subprocess, re, pathlib, shutil, sys, os, json

SRC  = pathlib.Path(__file__).resolve().parent
WORK = SRC / '.probrun'
CHROME = os.environ.get('CHROME') or next((c for c in [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe'),
] if pathlib.Path(c).exists()), None)
if not CHROME: sys.exit('kein Chrome')
if WORK.exists(): shutil.rmtree(WORK, ignore_errors=True)
shutil.copytree(SRC, WORK, dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('.git', '.testrun', '.probrun', '*.py', '*.md'))

TESTS = r"""
<script>
window.addEventListener('error', e => {
  if (document.getElementById('testout')) return;
  const pre = document.createElement('pre'); pre.id='testout';
  pre.textContent = 'ABBRUCH: ' + e.message + ' (Zeile ' + e.lineno + ')';
  document.body.appendChild(pre);
});
</script>
<script>
(async function(){
  const out=[];
  const t=(n,fn)=>{ try{ out.push(n+' -> '+JSON.stringify(fn())); }catch(e){ out.push(n+' ERR '+e.message); } };

  t('A: Fehlermeldung im Schritt list sichtbar?', ()=>{
    const vS=view, stS=foodStep, fS=foodFehler, kS=JSON.stringify(profile.kcal);
    profile.kcal={goal:2000, foods:[], meals:[]};
    view='food'; foodStep='list'; foodFehler='Kein Netz oder Datenbank nicht erreichbar.';
    renderFood();
    const h=app.innerHTML;
    view=vS; foodStep=stS; foodFehler=fS; profile.kcal=JSON.parse(kS);
    return {enthaeltMeldung: h.indexOf('Hat nicht geklappt')>-1,
            enthaeltText: h.indexOf('Kein Netz')>-1};
  });

  t('B: gibt es irgendwo data-delfood im gebauten Bild?', ()=>{
    const vS=view, stS=foodStep, tS=foodTab, kS=JSON.stringify(profile.kcal);
    profile.kcal={goal:2000, meals:[], foods:[{id:'a',name:'Quark',kcal:68,p:12,c:4,f:0,basis:'g100'}]};
    view='food'; foodStep='list'; foodTab='suchen'; renderFood(); renderFoodList('');
    const h=app.innerHTML;
    view=vS; foodStep=stS; foodTab=tS; profile.kcal=JSON.parse(kS);
    return {delfood: h.indexOf('data-delfood')>-1, quelle: (window.APP_QUELLE||'').indexOf('data-delfood="')>-1};
  });

  t('C: Reiterwechsel mit echtem Tippen', ()=>{
    const vS=view, stS=foodStep, tS=foodTab, qS=foodQ, kS=JSON.stringify(profile.kcal);
    profile.kcal={goal:2000, meals:[], foods:[{id:'a',name:'Quark',kcal:68,p:12,c:4,f:0,basis:'g100'}]};
    view='food'; foodStep='list'; foodTab='suchen'; foodQ='';
    renderFood();
    const feld=document.getElementById('foodSearch');
    feld.value='qua';
    feld.dispatchEvent(new Event('input',{bubbles:true}));
    const nachTippen=foodQ;
    // Reiter wechseln per echtem Klick
    app.querySelector('[data-act="foodtab:fav"]').click();
    const tabNach=foodTab;
    app.querySelector('[data-act="foodtab:suchen"]').click();
    const feld2=document.getElementById('foodSearch');
    const wert=feld2?feld2.value:null;
    view=vS; foodStep=stS; foodTab=tS; foodQ=qS; profile.kcal=JSON.parse(kS);
    return {foodQnachTippen:nachTippen, tabNachKlick:tabNach, feldWertZurueck:wert};
  });

  t('D: Stern-Klick traegt zusaetzlich ein?', ()=>{
    const vS=view, stS=foodStep, tS=foodTab, kS=JSON.stringify(profile.kcal);
    profile.kcal={goal:2000, meals:[], foods:[{id:'a',name:'Quark',kcal:68,p:12,c:4,f:0,basis:'g100'}]};
    view='food'; foodStep='list'; foodTab='suchen'; renderFood(); renderFoodList('');
    const stern=app.querySelector('[data-foodfav="a"]');
    stern.click();
    const r={schrittNachStern:foodStep, fav:!!kcalInit().foods[0].fav};
    view=vS; foodStep=stS; foodTab=tS; profile.kcal=JSON.parse(kS);
    return r;
  });

  t('E: Stern unter Favoriten -> Liste danach', ()=>{
    const vS=view, stS=foodStep, tS=foodTab, kS=JSON.stringify(profile.kcal);
    profile.kcal={goal:2000, meals:[], foods:[
      {id:'a',name:'Quark',kcal:68,p:12,c:4,f:0,basis:'g100',fav:true},
      {id:'b',name:'Butter',kcal:740,p:0,c:0,f:82,basis:'g100',fav:true}]};
    view='food'; foodStep='list'; foodTab='fav'; renderFood();
    const stern=app.querySelector('[data-foodfav="a"]');
    stern.click();
    const h=document.getElementById('foodList').innerHTML;
    const zahl=document.getElementById('foodZahl');
    const r={nochQuarkInListe: h.indexOf('Quark')>-1, zahl: zahl?zahl.textContent:null};
    view=vS; foodStep=stS; foodTab=tS; profile.kcal=JSON.parse(kS);
    return r;
  });

  t('F: Zuletzt-Reiter, Suchtext gesetzt', ()=>{
    const vS=view, stS=foodStep, tS=foodTab, qS=foodQ, kS=JSON.stringify(profile.kcal);
    profile.kcal={goal:2000, foods:[{id:'a',name:'Quark',kcal:68,p:12,c:4,f:0,basis:'g100'}],
      meals:[{id:'m1',name:'Quark',kcal:170,date:Date.now()}]};
    view='food'; foodStep='list'; foodTab='zuletzt'; foodQ='butter'; renderFood();
    const h=document.getElementById('foodList').innerHTML;
    const dbknopf=app.querySelector('[data-act="food:dbsuche"]');
    const r={zeigtQuark:h.indexOf('Quark')>-1, dbKnopfDa:!!dbknopf};
    view=vS; foodStep=stS; foodTab=tS; foodQ=qS; profile.kcal=JSON.parse(kS);
    return r;
  });

  t('G: Zaehler bei leerer Liste', ()=>{
    const vS=view, stS=foodStep, tS=foodTab, kS=JSON.stringify(profile.kcal);
    profile.kcal={goal:2000, meals:[], foods:[]};
    view='food'; foodStep='list'; foodTab='suchen'; renderFood();
    const z=document.getElementById('foodZahl');
    const r={zahl:z?JSON.stringify(z.textContent):null};
    view=vS; foodStep=stS; foodTab=tS; profile.kcal=JSON.parse(kS);
    return r;
  });

  t('H: foodmz kommt in der App ueberhaupt vor?', ()=>{
    const q=window.APP_QUELLE||'';
    return {foodmz: q.indexOf('foodmz:')>-1};
  });

  const pre=document.createElement('pre'); pre.id='testout';
  pre.textContent=out.join('\n'); document.body.appendChild(pre);
})();
</script>
"""

html = (WORK / 'index.html').read_text(encoding='utf-8')
SW_TXT = (WORK / 'sw.js').read_text(encoding='utf-8')
SW_BLOCK = '<script>window.SW_QUELLE = ' + json.dumps(SW_TXT) + ';</script>' + chr(10)
SQL_TXT = {f.name: f.read_text(encoding='utf-8') for f in sorted(WORK.glob('supabase-*.sql'))}
SQL_BLOCK = '<script>window.SQL_QUELLEN = ' + json.dumps(SQL_TXT) + ';</script>' + chr(10)
APP_BLOCK = ('<script>window.APP_QUELLE = ' + json.dumps(html).replace('</', r'<\/')
             + ';</script>' + chr(10))
(WORK / 'probe.html').write_text(html + SW_BLOCK + SQL_BLOCK + APP_BLOCK + TESTS, encoding='utf-8')

r = subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
                    '--virtual-time-budget=45000', '--allow-file-access-from-files',
                    '--dump-dom', (WORK / 'probe.html').as_uri()],
                   capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
m = re.search(r'<pre id="testout">(.*?)</pre>', r.stdout, re.S)
enc = sys.stdout.encoding or 'utf-8'
def zeigen(s): print(s.encode(enc, errors='replace').decode(enc, errors='replace'))
if not m:
    zeigen('Kein Ergebnis.'); zeigen(r.stdout[-3000:]); zeigen(r.stderr[-2000:]); sys.exit(1)
txt = m.group(1).replace('&amp;','&').replace('&lt;','<').replace('&gt;','>').replace('&quot;','"')
zeigen(txt)
