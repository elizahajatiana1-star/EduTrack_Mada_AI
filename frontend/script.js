// =================================================================
// EduTrack Madagascar AI — Interface (Personne 4)
// Câblé sur le contrat d'API décrit dans le cahier des charges (§4.4)
// =================================================================
//
// Rappel du contrat d'API (cahier des charges §4.4) :
//   GET    /api/eleves                          -> liste des élèves
//   POST   /api/eleves                           -> créer un élève
//   PUT    /api/eleves/{id}                       -> modifier un élève
//   DELETE /api/eleves/{id}                       -> supprimer un élève
//   POST   /api/notes                             -> ajouter une note
//   POST   /api/absences                          -> ajouter une absence
//   GET    /api/eleves/{id}/score                 -> score de risque (Module IA)
//   GET    /api/alertes                           -> liste des alertes actives
//   GET    /api/eleves/{id}/recommandations       -> recommandations pour l'élève
//
// Hypothèse (à confirmer avec Personne 1 / Personne 2) : GET /api/eleves
// renvoie chaque élève avec ses notes et absences imbriquées (relations
// SQLAlchemy sérialisées). Si votre backend expose plutôt des routes
// séparées, adaptez uniquement fetchStudents() plus bas.

const API_BASE_URL = "http://localhost:5000/api"; // <-- URL de votre backend

const ENDPOINTS = {
  list:   ()        => `${API_BASE_URL}/eleves`,
  create: ()         => `${API_BASE_URL}/eleves`,
  update: (id)       => `${API_BASE_URL}/eleves/${id}`,
  remove: (id)       => `${API_BASE_URL}/eleves/${id}`,
  addNote:     ()    => `${API_BASE_URL}/notes`,
  addAbsence:  ()    => `${API_BASE_URL}/absences`,
  score:  (id)       => `${API_BASE_URL}/eleves/${id}/score`,
  alertes:()         => `${API_BASE_URL}/alertes`,
  reco:   (id)       => `${API_BASE_URL}/eleves/${id}/recommandations`,
};

// -----------------------------------------------------------------
// Mapping API <-> modèle interne. C'est le SEUL endroit à modifier
// si les noms de champs du backend diffèrent (ex: "moyenne_generale").
// -----------------------------------------------------------------
function mapFromApi(apiObj){
  return {
    id: apiObj.id,
    name: apiObj.nom ?? apiObj.name ?? "",
    cls: apiObj.classe ?? apiObj.cls ?? "",
    contact: apiObj.contact_parent ?? apiObj.contact ?? "",
    notes: (apiObj.notes ?? []).map(n=>({
      id: n.id ?? null,
      subject: n.matiere ?? n.subject ?? "",
      value: Number(n.valeur ?? n.value ?? 0),
      date: n.date ?? null,
    })),
    absences: (apiObj.absences ?? []).map(a=>({
      id: a.id ?? null,
      date: a.date ?? null,
      justified: Boolean(a.justifiee ?? a.justified ?? false),
    })),
    apiRisk: null,   // rempli plus tard par enrichWithApiScores()
    apiReco: null,   // rempli plus tard par enrichWithApiScores()
  };
}

function mapStudentToApi(student){
  return {
    nom: student.name,
    classe: student.cls,
    contact_parent: student.contact,
  };
}
function mapNoteToApi(eleveId, note){
  return { eleve_id: eleveId, matiere: note.subject, valeur: note.value, date: note.date };
}
function mapAbsenceToApi(eleveId, absence){
  return { eleve_id: eleveId, date: absence.date, justifiee: absence.justified };
}

async function apiRequest(url, options={}){
  const res = await fetch(url, { headers: { "Content-Type": "application/json" }, ...options });
  if(!res.ok){
    const text = await res.text().catch(()=> "");
    throw new Error(`Erreur API (${res.status}) sur ${url}${text ? " — " + text : ""}`);
  }
  if(res.status === 204) return null;
  return res.json();
}

async function fetchStudents(){
  const data = await apiRequest(ENDPOINTS.list());
  return (Array.isArray(data) ? data : data.eleves ?? []).map(mapFromApi);
}
async function apiCreateStudent(student){
  const data = await apiRequest(ENDPOINTS.create(), { method:"POST", body: JSON.stringify(mapStudentToApi(student)) });
  return mapFromApi(data);
}
async function apiUpdateStudent(id, student){
  const data = await apiRequest(ENDPOINTS.update(id), { method:"PUT", body: JSON.stringify(mapStudentToApi(student)) });
  return mapFromApi(data);
}
async function apiDeleteStudent(id){
  await apiRequest(ENDPOINTS.remove(id), { method:"DELETE" });
}
async function apiAddNote(eleveId, note){
  return apiRequest(ENDPOINTS.addNote(), { method:"POST", body: JSON.stringify(mapNoteToApi(eleveId, note)) });
}
async function apiAddAbsence(eleveId, absence){
  return apiRequest(ENDPOINTS.addAbsence(), { method:"POST", body: JSON.stringify(mapAbsenceToApi(eleveId, absence)) });
}
// Enrichissement optionnel : si le Module d'analyse (IA — Personne 3) expose
// déjà /score et /recommandations, on les utilise en priorité. Si les routes
// ne répondent pas encore, l'appli continue avec le calcul local (§5).
async function enrichWithApiScores(){
  await Promise.allSettled(students.map(async (s)=>{
    try{
      const score = await apiRequest(ENDPOINTS.score(s.id));
      s.apiRisk = score.niveau ?? score.risk_level ?? null;
    }catch(e){ /* pas grave : fallback local */ }
    try{
      const reco = await apiRequest(ENDPOINTS.reco(s.id));
      s.apiReco = Array.isArray(reco) ? reco : (reco.recommandations ?? null);
    }catch(e){ /* pas grave : fallback local */ }
  }));
  render();
}

// ---------------------------------------------------------------
// État de l'application
// ---------------------------------------------------------------
let students = [];
let activeTab = "dashboard";
let classFilter = "all";
let historyStudentId = null;
let isLoading = true;
let apiError = null;
let isSaving = false;
// modal = { type: null | "student" | "note" | "absence", id: number|null }
let modal = { type: null, id: null };

async function loadStudents(){
  isLoading = true; apiError = null; render();
  try{
    students = await fetchStudents();
    if(students.length && historyStudentId===null) historyStudentId = students[0].id;
  }catch(err){
    apiError = err.message || "Impossible de contacter l'API.";
    students = [];
  }finally{
    isLoading = false;
    render();
  }
  if(students.length) enrichWithApiScores();
}

// ---------------------------------------------------------------
// Moteur de scoring — reproduit exactement le §5 du cahier des charges
// (utilisé seulement si le backend n'a pas encore répondu sur /score)
// ---------------------------------------------------------------
function average(s){
  if(!s.notes.length) return 0;
  return s.notes.reduce((a,n)=>a+n.value,0)/s.notes.length;
}
function absenceCount(s){ return s.absences.length; }

function riskLevel(s){
  if(s.apiRisk === "risk" || s.apiRisk === "warn" || s.apiRisk === "ok") return s.apiRisk;
  if(s.apiRisk === "Risque élevé") return "risk";
  if(s.apiRisk === "À surveiller") return "warn";
  if(s.apiRisk === "Stable") return "ok";

  const avg = average(s);
  let score = 0;
  if(avg < 8) score += 3; else if(avg < 10) score += 2; else if(avg < 12) score += 1;
  const abs = absenceCount(s);
  if(abs >= 8) score += 3; else if(abs >= 4) score += 2; else if(abs >= 2) score += 1;
  if(score >= 4) return "risk";
  if(score >= 2) return "warn";
  return "ok";
}
function riskLabel(level){
  return level==="risk" ? "Risque élevé" : level==="warn" ? "À surveiller" : "Stable";
}
function weakestSubjects(s){
  return [...s.notes].sort((a,b)=>a.value-b.value).slice(0,2).filter(n=>n.value<12);
}
function recommendations(s){
  if(Array.isArray(s.apiReco) && s.apiReco.length) return s.apiReco;
  const level = riskLevel(s);
  const weak = weakestSubjects(s);
  const recs = [];
  weak.forEach(n=> recs.push(`Renforcer ${n.subject} (moyenne ${n.value.toFixed(1)}/20) — prévoir des exercices ciblés.`));
  if(absenceCount(s) >= 4) recs.push(`Contacter la famille au sujet des absences (${absenceCount(s)} sur la période).`);
  if(level === "risk") recs.push("Proposer un entretien enseignant-parent sous 7 jours.");
  if(recs.length===0) recs.push("Aucune action urgente — poursuivre le suivi habituel.");
  return recs;
}
function fmtDate(d){
  if(!d) return "—";
  const dt = new Date(d);
  if(isNaN(dt)) return d;
  return dt.toLocaleDateString('fr-FR', {day:'2-digit', month:'2-digit', year:'numeric'});
}

// ---------------------------------------------------------------
// Rendu
// ---------------------------------------------------------------
function render(){
  const root = document.getElementById('root');
  root.innerHTML = `
    <div class="app">
      ${renderSidebar()}
      <div class="main">
        ${renderApiBanner()}
        ${activeTab==="dashboard" ? renderDashboard() : ""}
        ${activeTab==="students" ? renderStudents() : ""}
        ${activeTab==="alerts" ? renderAlerts() : ""}
        ${activeTab==="reco" ? renderReco() : ""}
        ${activeTab==="history" ? renderHistory() : ""}
      </div>
    </div>
    ${renderModal()}
  `;
  attachEvents();
}

function renderApiBanner(){
  if(isLoading){
    return `<div class="api-banner loading"><span class="spin"></span> Connexion à l'API — chargement des élèves…</div>`;
  }
  if(apiError){
    return `<div class="api-banner error">⚠ ${apiError} — vérifiez que le backend tourne sur <code>${API_BASE_URL}</code> et autorise le CORS.
      <button data-action="retry-load">Réessayer</button></div>`;
  }
  return "";
}

function renderSidebar(){
  const items = [
    {id:"dashboard", num:"01", label:"Tableau de bord"},
    {id:"students", num:"02", label:"Élèves"},
    {id:"alerts", num:"03", label:"Alertes"},
    {id:"reco", num:"04", label:"Recommandations"},
    {id:"history", num:"05", label:"Historique"},
  ];
  return `
  <div class="sidebar">
    <div class="brand">
      <div class="mark">Edu<span>Track</span></div>
      <div class="sub">Madagascar · AI</div>
    </div>
    ${items.map(it=>`
      <div class="nav-item ${activeTab===it.id?'active':''}" data-tab="${it.id}">
        <span class="num">${it.num}</span>${it.label}
      </div>
    `).join('')}
    <div class="sidebar-foot">v0.2 — branché sur l'API<br/>scoring rule-based (§5) + IA optionnelle</div>
  </div>`;
}

function renderDashboard(){
  const total = students.length;
  const riskCount = students.filter(s=>riskLevel(s)==="risk").length;
  const warnCount = students.filter(s=>riskLevel(s)==="warn").length;
  const okCount = students.filter(s=>riskLevel(s)==="ok").length;
  const rows = students.slice().sort((a,b)=>{
    const order = {risk:0, warn:1, ok:2};
    return order[riskLevel(a)] - order[riskLevel(b)];
  });

  return `
  <div class="page-head">
    <div>
      <span class="eyebrow">Vue d'ensemble</span>
      <h1>Tableau de bord pédagogique</h1>
      <p>Suivi centralisé des notes, absences et détection automatique des élèves en difficulté.</p>
    </div>
    <div style="display:flex; gap:10px;">
      <button class="btn ghost" data-action="retry-load">↻ Actualiser</button>
      <button class="btn" data-action="new-student">+ Nouvel élève</button>
    </div>
  </div>

  <div class="stats-row">
    <div class="stat"><div class="label">Élèves suivis</div><div class="value">${total}</div></div>
    <div class="stat risk"><div class="label">Risque élevé</div><div class="value">${riskCount}</div></div>
    <div class="stat warn"><div class="label">À surveiller</div><div class="value">${warnCount}</div></div>
    <div class="stat ok"><div class="label">Stables</div><div class="value">${okCount}</div></div>
  </div>

  <div class="ledger">
    <h2>Registre des élèves <span class="tag">tri par risque</span></h2>
    ${total===0 ? `<div class="empty">Aucun élève pour le moment.</div>` : `
    <table>
      <thead><tr><th>Élève</th><th>Classe</th><th>Moyenne</th><th>Absences</th><th>Statut</th></tr></thead>
      <tbody>
        ${rows.map(s=>{
          const level = riskLevel(s);
          return `<tr>
            <td class="name-cell">${s.name}</td>
            <td class="class-tag">${s.cls}</td>
            <td class="avg-mono">${average(s).toFixed(1)}/20</td>
            <td class="avg-mono">${absenceCount(s)}</td>
            <td><span class="stamp ${level}"><span class="dot"></span>${riskLabel(level)}</span></td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>`}
  </div>
  `;
}

function renderStudents(){
  const classes = ["all", ...new Set(students.map(s=>s.cls))];
  const filtered = classFilter==="all" ? students : students.filter(s=>s.cls===classFilter);
  return `
  <div class="page-head">
    <div>
      <span class="eyebrow">Gestion</span>
      <h1>Élèves</h1>
      <p>Fiche élève (nom, classe, contact du parent §3.1). Ajout des notes et absences via les actions dédiées.</p>
    </div>
    <button class="btn" data-action="new-student">+ Nouvel élève</button>
  </div>

  <div class="ledger">
    <h2>Liste des élèves <span class="tag">${filtered.length} au total</span></h2>
    <div style="margin-bottom:14px;">
      <select class="filter" id="class-filter">
        ${classes.map(c=>`<option value="${c}" ${classFilter===c?'selected':''}>${c==="all"?"Toutes les classes":c}</option>`).join('')}
      </select>
    </div>
    ${filtered.length===0 ? `<div class="empty">Aucun élève dans cette classe.</div>` : `
    <table>
      <thead><tr><th>Élève</th><th>Classe</th><th>Contact parent</th><th>Matières</th><th>Moyenne</th><th>Absences</th><th>Statut</th><th></th></tr></thead>
      <tbody>
        ${filtered.map(s=>{
          const level = riskLevel(s);
          return `<tr>
            <td class="name-cell">${s.name}</td>
            <td class="class-tag">${s.cls}</td>
            <td class="contact-cell">${s.contact || "—"}</td>
            <td>${s.notes.map(n=>`<span class="subject-pill">${n.subject} ${n.value}</span>`).join('') || '<span class="empty-inline">Aucune note</span>'}</td>
            <td class="avg-mono">${average(s).toFixed(1)}/20</td>
            <td class="avg-mono">${absenceCount(s)}</td>
            <td><span class="stamp ${level}"><span class="dot"></span>${riskLabel(level)}</span></td>
            <td>
              <div class="action-group">
                <button class="btn ghost small" data-action="edit" data-id="${s.id}">Modifier</button>
                <button class="btn ghost small" data-action="add-note" data-id="${s.id}">+ Note</button>
                <button class="btn ghost small" data-action="add-absence" data-id="${s.id}">+ Absence</button>
                <button class="btn danger small" data-action="delete" data-id="${s.id}">Suppr.</button>
              </div>
            </td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>`}
  </div>
  `;
}

function renderAlerts(){
  const flagged = students.filter(s=>riskLevel(s)!=="ok").sort((a,b)=>{
    const order={risk:0,warn:1}; return order[riskLevel(a)]-order[riskLevel(b)];
  });
  return `
  <div class="page-head">
    <div>
      <span class="eyebrow">Détection</span>
      <h1>Alertes de décrochage</h1>
      <p>Élèves signalés automatiquement par le module de scoring (moyenne faible et/ou absences répétées — §5).</p>
    </div>
  </div>
  <div class="ledger">
    <h2>Élèves signalés <span class="tag">${flagged.length}</span></h2>
    ${flagged.length===0 ? `<div class="empty">Aucune alerte active — tous les élèves sont stables.</div>` :
      flagged.map(s=>{
        const level = riskLevel(s);
        const reasons = [];
        if(average(s) < 10) reasons.push(`moyenne générale faible (${average(s).toFixed(1)}/20)`);
        if(absenceCount(s) >= 4) reasons.push(`${absenceCount(s)} absences enregistrées`);
        return `<div class="alert-card ${level==='warn'?'warn':''}">
          <div>
            <div class="who">${s.name} — ${s.cls}</div>
            <div class="why">Motif : ${reasons.join(', ') || 'score combiné élevé'}.</div>
          </div>
          <span class="stamp ${level}"><span class="dot"></span>${riskLabel(level)}</span>
        </div>`;
      }).join('')
    }
  </div>
  `;
}

function renderReco(){
  const list = students.slice().sort((a,b)=>{
    const order={risk:0,warn:1,ok:2}; return order[riskLevel(a)]-order[riskLevel(b)];
  });
  return `
  <div class="page-head">
    <div>
      <span class="eyebrow">Accompagnement</span>
      <h1>Recommandations pédagogiques</h1>
      <p>Suggestions générées à partir des matières faibles et du taux d'absentéisme (§3.5).</p>
    </div>
  </div>
  <div class="ledger">
    <h2>Par élève</h2>
    ${list.length===0 ? `<div class="empty">Aucun élève pour le moment.</div>` : list.map(s=>{
      const level = riskLevel(s);
      return `<div class="alert-card" style="border-left-color:${level==='ok'?'var(--stamp-green)':level==='warn'?'var(--stamp-amber)':'var(--stamp-red)'}">
        <div style="flex:1;">
          <div class="who">${s.name} — ${s.cls}</div>
          <ul class="reco-list">
            ${recommendations(s).map(r=>`<li>${r}</li>`).join('')}
          </ul>
        </div>
        <span class="stamp ${level}"><span class="dot"></span>${riskLabel(level)}</span>
      </div>`;
    }).join('')}
  </div>
  `;
}

function renderHistory(){
  if(students.length===0){
    return `
    <div class="page-head">
      <div><span class="eyebrow">Suivi</span><h1>Historique scolaire</h1></div>
    </div>
    <div class="ledger"><div class="empty">Aucun élève pour le moment.</div></div>`;
  }
  const student = students.find(s=>s.id===historyStudentId) ?? students[0];
  const notesSorted = [...student.notes].sort((a,b)=> new Date(a.date||0) - new Date(b.date||0));
  const absencesSorted = [...student.absences].sort((a,b)=> new Date(b.date||0) - new Date(a.date||0));

  // moyenne cumulative dans le temps, pour observer une tendance (§3.6)
  let running = 0;
  const trendPoints = notesSorted.map((n,i)=>{
    running += n.value;
    return running/(i+1);
  });

  return `
  <div class="page-head">
    <div>
      <span class="eyebrow">Suivi</span>
      <h1>Historique scolaire</h1>
      <p>Évolution des moyennes et des absences dans le temps, pour repérer une tendance plutôt qu'une note isolée.</p>
    </div>
  </div>

  <div class="ledger">
    <h2>Sélection de l'élève</h2>
    <select class="filter" id="history-select">
      ${students.map(s=>`<option value="${s.id}" ${s.id===student.id?'selected':''}>${s.name} — ${s.cls}</option>`).join('')}
    </select>
  </div>

  <div class="stats-row">
    <div class="stat"><div class="label">Moyenne actuelle</div><div class="value">${average(student).toFixed(1)}</div></div>
    <div class="stat"><div class="label">Notes enregistrées</div><div class="value">${student.notes.length}</div></div>
    <div class="stat warn"><div class="label">Absences</div><div class="value">${absenceCount(student)}</div></div>
    <div class="stat ${riskLevel(student)}"><div class="label">Statut</div><div class="value" style="font-size:16px;">${riskLabel(riskLevel(student))}</div></div>
  </div>

  <div class="ledger">
    <h2>Tendance de la moyenne <span class="tag">${notesSorted.length} points</span></h2>
    ${trendPoints.length < 2 ? `<div class="empty">Ajoutez au moins deux notes datées pour visualiser une tendance.</div>` :
      renderTrendSvg(trendPoints)}
  </div>

  <div class="ledger">
    <h2>Notes <span class="tag">${notesSorted.length}</span></h2>
    ${notesSorted.length===0 ? `<div class="empty">Aucune note enregistrée.</div>` : `
    <table>
      <thead><tr><th>Date</th><th>Matière</th><th>Note</th></tr></thead>
      <tbody>
        ${notesSorted.slice().reverse().map(n=>`<tr><td>${fmtDate(n.date)}</td><td>${n.subject}</td><td class="avg-mono">${n.value}/20</td></tr>`).join('')}
      </tbody>
    </table>`}
  </div>

  <div class="ledger">
    <h2>Absences <span class="tag">${absencesSorted.length}</span></h2>
    ${absencesSorted.length===0 ? `<div class="empty">Aucune absence enregistrée.</div>` : `
    <table>
      <thead><tr><th>Date</th><th>Statut</th></tr></thead>
      <tbody>
        ${absencesSorted.map(a=>`<tr><td>${fmtDate(a.date)}</td><td>${a.justified ? '<span class="stamp ok"><span class="dot"></span>Justifiée</span>' : '<span class="stamp risk"><span class="dot"></span>Non justifiée</span>'}</td></tr>`).join('')}
      </tbody>
    </table>`}
  </div>
  `;
}

function renderTrendSvg(points){
  const w = 560, h = 120, pad = 16;
  const max = 20, min = 0;
  const stepX = points.length>1 ? (w-2*pad)/(points.length-1) : 0;
  const coords = points.map((v,i)=>{
    const x = pad + i*stepX;
    const y = h - pad - ((v-min)/(max-min))*(h-2*pad);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const last = points[points.length-1];
  return `
  <div class="trend-wrap">
    <svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}">
      <line x1="${pad}" y1="${h-pad-((10-min)/(max-min))*(h-2*pad)}" x2="${w-pad}" y2="${h-pad-((10-min)/(max-min))*(h-2*pad)}" stroke="var(--line)" stroke-dasharray="4 4"/>
      <polyline points="${coords.join(' ')}" fill="none" stroke="var(--margin-red)" stroke-width="2"/>
      ${coords.map(c=>{ const [x,y]=c.split(','); return `<circle cx="${x}" cy="${y}" r="3" fill="var(--margin-red)"/>`; }).join('')}
    </svg>
    <div class="trend-legend">Moyenne cumulative actuelle : <strong>${last.toFixed(1)}/20</strong> — ligne pointillée = seuil 10/20</div>
  </div>`;
}

function renderModal(){
  if(modal.type === "student") return renderStudentModal();
  if(modal.type === "note") return renderNoteModal();
  if(modal.type === "absence") return renderAbsenceModal();
  return `<div class="overlay" id="overlay"></div>`;
}

function renderStudentModal(){
  const editing = modal.id ? students.find(s=>s.id===modal.id) : null;
  return `
  <div class="overlay show" id="overlay">
    <div class="modal">
      <h3>${editing ? "Modifier l'élève" : "Nouvel élève"}</h3>
      <div class="field">
        <label>Nom complet</label>
        <input id="f-name" value="${editing? editing.name:''}" placeholder="Ex : Fara Ranaivo"/>
      </div>
      <div class="field">
        <label>Classe</label>
        <input id="f-cls" value="${editing? editing.cls:''}" placeholder="Ex : 5e A"/>
      </div>
      <div class="field">
        <label>Contact du parent</label>
        <input id="f-contact" value="${editing? editing.contact:''}" placeholder="Téléphone ou email"/>
      </div>
      <div class="modal-actions">
        <button class="btn ghost" data-action="close-modal">Annuler</button>
        <button class="btn" data-action="save-student">Enregistrer</button>
      </div>
    </div>
  </div>`;
}

function renderNoteModal(){
  const s = students.find(x=>x.id===modal.id);
  const today = new Date().toISOString().slice(0,10);
  return `
  <div class="overlay show" id="overlay">
    <div class="modal">
      <h3>Nouvelle note — ${s ? s.name : ''}</h3>
      <div class="field">
        <label>Matière</label>
        <input id="f-note-subject" placeholder="Ex : Mathématiques"/>
      </div>
      <div class="field">
        <label>Note /20</label>
        <input id="f-note-value" type="number" min="0" max="20" step="0.5"/>
      </div>
      <div class="field">
        <label>Date</label>
        <input id="f-note-date" type="date" value="${today}"/>
      </div>
      <div class="modal-actions">
        <button class="btn ghost" data-action="close-modal">Annuler</button>
        <button class="btn" data-action="save-note">Enregistrer</button>
      </div>
    </div>
  </div>`;
}

function renderAbsenceModal(){
  const s = students.find(x=>x.id===modal.id);
  const today = new Date().toISOString().slice(0,10);
  return `
  <div class="overlay show" id="overlay">
    <div class="modal">
      <h3>Nouvelle absence — ${s ? s.name : ''}</h3>
      <div class="field">
        <label>Date</label>
        <input id="f-abs-date" type="date" value="${today}"/>
      </div>
      <div class="field">
        <label><input id="f-abs-justified" type="checkbox" style="width:auto; margin-right:8px;"/>Absence justifiée</label>
      </div>
      <div class="modal-actions">
        <button class="btn ghost" data-action="close-modal">Annuler</button>
        <button class="btn" data-action="save-absence">Enregistrer</button>
      </div>
    </div>
  </div>`;
}

function closeModal(){ modal = { type:null, id:null }; render(); }

function attachEvents(){
  document.querySelectorAll('.nav-item').forEach(el=>{
    el.onclick = ()=>{ activeTab = el.dataset.tab; render(); };
  });

  document.querySelectorAll('[data-action="new-student"]').forEach(b=>{
    b.onclick = ()=>{ modal = { type:"student", id:null }; render(); };
  });
  document.querySelectorAll('[data-action="edit"]').forEach(b=>{
    b.onclick = ()=>{ modal = { type:"student", id: parseInt(b.dataset.id) }; render(); };
  });
  document.querySelectorAll('[data-action="add-note"]').forEach(b=>{
    b.onclick = ()=>{ modal = { type:"note", id: parseInt(b.dataset.id) }; render(); };
  });
  document.querySelectorAll('[data-action="add-absence"]').forEach(b=>{
    b.onclick = ()=>{ modal = { type:"absence", id: parseInt(b.dataset.id) }; render(); };
  });
  document.querySelectorAll('[data-action="delete"]').forEach(b=>{
    b.onclick = async ()=>{
      const id = parseInt(b.dataset.id);
      if(!confirm("Supprimer définitivement cet élève ?")) return;
      const previous = students;
      students = students.filter(s=>s.id!==id);
      render();
      try{ await apiDeleteStudent(id); }
      catch(err){ students = previous; apiError = err.message || "Échec de la suppression."; render(); }
    };
  });

  const closeBtn = document.querySelector('[data-action="close-modal"]');
  if(closeBtn) closeBtn.onclick = closeModal;

  const overlay = document.getElementById('overlay');
  if(overlay) overlay.onclick = (e)=>{ if(e.target===overlay) closeModal(); };

  const saveStudentBtn = document.querySelector('[data-action="save-student"]');
  if(saveStudentBtn) saveStudentBtn.onclick = async ()=>{
    if(isSaving) return;
    const name = document.getElementById('f-name').value.trim();
    const cls = document.getElementById('f-cls').value.trim();
    const contact = document.getElementById('f-contact').value.trim();
    if(!name || !cls) return;
    isSaving = true; saveStudentBtn.textContent = "Enregistrement…"; saveStudentBtn.disabled = true;
    try{
      if(modal.id){
        const current = students.find(x=>x.id===modal.id);
        const draft = { ...current, name, cls, contact };
        const saved = await apiUpdateStudent(modal.id, draft);
        Object.assign(current, saved, { notes: current.notes, absences: current.absences });
      } else {
        const created = await apiCreateStudent({ name, cls, contact });
        created.notes = created.notes ?? [];
        created.absences = created.absences ?? [];
        students.push(created);
      }
      apiError = null;
      closeModal();
    }catch(err){
      apiError = err.message || "Échec de l'enregistrement.";
      render();
    }finally{ isSaving = false; }
  };

  const saveNoteBtn = document.querySelector('[data-action="save-note"]');
  if(saveNoteBtn) saveNoteBtn.onclick = async ()=>{
    const subject = document.getElementById('f-note-subject').value.trim();
    const value = parseFloat(document.getElementById('f-note-value').value);
    const date = document.getElementById('f-note-date').value;
    if(!subject || isNaN(value)) return;
    const student = students.find(s=>s.id===modal.id);
    const note = { subject, value, date };
    try{
      const saved = await apiAddNote(modal.id, note);
      student.notes.push({
        id: saved?.id ?? null,
        subject: saved?.matiere ?? subject,
        value: Number(saved?.valeur ?? value),
        date: saved?.date ?? date,
      });
      apiError = null;
      closeModal();
    }catch(err){
      apiError = err.message || "Échec de l'ajout de la note.";
      render();
    }
  };

  const saveAbsenceBtn = document.querySelector('[data-action="save-absence"]');
  if(saveAbsenceBtn) saveAbsenceBtn.onclick = async ()=>{
    const date = document.getElementById('f-abs-date').value;
    const justified = document.getElementById('f-abs-justified').checked;
    if(!date) return;
    const student = students.find(s=>s.id===modal.id);
    const absence = { date, justified };
    try{
      const saved = await apiAddAbsence(modal.id, absence);
      student.absences.push({
        id: saved?.id ?? null,
        date: saved?.date ?? date,
        justified: Boolean(saved?.justifiee ?? justified),
      });
      apiError = null;
      closeModal();
    }catch(err){
      apiError = err.message || "Échec de l'ajout de l'absence.";
      render();
    }
  };

  const classFilterSel = document.getElementById('class-filter');
  if(classFilterSel) classFilterSel.onchange = (e)=>{ classFilter = e.target.value; render(); };

  const historySel = document.getElementById('history-select');
  if(historySel) historySel.onchange = (e)=>{ historyStudentId = parseInt(e.target.value); render(); };

  const retryBtn = document.querySelector('[data-action="retry-load"]');
  if(retryBtn) retryBtn.onclick = ()=> loadStudents();
}

loadStudents();
