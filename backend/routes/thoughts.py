<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Thoughts · Noema</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=DM+Mono:wght@300;400&family=Syne:wght@300;400;500;600&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --void:#03040a;--deep:#07090f;--surface:#0d1018;
  --glass:rgba(255,255,255,0.04);--glass2:rgba(255,255,255,0.07);
  --border:rgba(255,255,255,0.08);--border2:rgba(255,255,255,0.14);
  --text:#e8e4dc;--muted:#7a7672;--accent:#c8a97e;--accent2:#8bb5c8;
}
html{scroll-behavior:smooth;font-size:16px}
body{background:var(--void);color:var(--text);font-family:'Syne',sans-serif;min-height:100vh;overflow-x:hidden}
#bg-canvas{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;opacity:.5}

nav{
  position:fixed;top:0;left:0;right:0;z-index:100;
  display:flex;align-items:center;justify-content:space-between;
  padding:1.2rem 3rem;border-bottom:1px solid var(--border);
  backdrop-filter:blur(24px);background:rgba(3,4,10,0.7);
}
.logo{font-family:'Cormorant Garamond',serif;font-size:1.6rem;font-weight:300;letter-spacing:.12em;color:var(--text);text-decoration:none}
.logo span{color:var(--accent)}
.nav-right{display:flex;align-items:center;gap:1.5rem}
.nav-link{font-size:.78rem;letter-spacing:.14em;color:var(--muted);cursor:pointer;text-transform:uppercase;transition:color .3s;text-decoration:none}
.nav-link:hover{color:var(--text)}
.nav-back{
  font-family:'Syne',sans-serif;font-size:.78rem;letter-spacing:.1em;text-transform:uppercase;
  padding:.55rem 1.4rem;border:1px solid var(--border2);background:var(--glass);
  color:var(--text);cursor:pointer;transition:all .3s;border-radius:2px;
  text-decoration:none;display:inline-flex;align-items:center;gap:.5rem;
}
.nav-back:hover{background:var(--glass2);border-color:var(--accent)}

.thoughts-hero{
  min-height:65vh;display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  text-align:center;padding:8rem 2rem 4rem;
  position:relative;z-index:1;
}
.hero-eyebrow{
  font-family:'DM Mono',monospace;font-size:.72rem;letter-spacing:.22em;
  color:var(--accent);text-transform:uppercase;margin-bottom:2rem;opacity:.8;
}
.hero-title{
  font-family:'Cormorant Garamond',serif;
  font-size:clamp(3rem,7vw,6rem);font-weight:300;line-height:1.05;
  letter-spacing:-.01em;margin-bottom:1.5rem;
  background:linear-gradient(160deg,#e8e4dc 30%,#c8a97e 70%,#8bb5c8 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.hero-title em{font-style:italic;font-weight:300}
.hero-sub{font-size:1rem;line-height:1.8;color:var(--muted);max-width:500px;font-weight:300}

.filter-bar{
  position:relative;z-index:1;padding:2.5rem 2rem;
  border-top:1px solid var(--border);border-bottom:1px solid var(--border);
  background:var(--deep);display:flex;align-items:center;gap:1.5rem;
  flex-wrap:wrap;justify-content:center;
}
.filter-label{font-family:'DM Mono',monospace;font-size:.62rem;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);flex-shrink:0}
.filter-tags{display:flex;flex-wrap:wrap;gap:.5rem;justify-content:center}
.filter-tag{
  font-family:'DM Mono',monospace;font-size:.68rem;letter-spacing:.12em;
  padding:.45rem 1rem;border:1px solid var(--border2);color:var(--muted);
  cursor:pointer;border-radius:2px;transition:all .3s;text-transform:uppercase;
}
.filter-tag:hover,.filter-tag.active{color:var(--text);border-color:var(--accent);background:rgba(200,169,126,.08)}

.thoughts-section{position:relative;z-index:1;padding:5rem 2rem}
.thoughts-grid{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));
  gap:1px;max-width:1200px;margin:0 auto;border:1px solid var(--border);
}

.thought-card{
  padding:2.2rem;background:var(--surface);
  border-right:1px solid var(--border);border-bottom:1px solid var(--border);
  cursor:pointer;transition:background .3s;position:relative;overflow:hidden;
}
.thought-card::after{
  content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,var(--accent),transparent);
  opacity:0;transition:opacity .4s;
}
.thought-card:hover{background:rgba(200,169,126,.03)}
.thought-card:hover::after{opacity:1}
.tc-cat{
  font-family:'DM Mono',monospace;font-size:.6rem;letter-spacing:.16em;
  color:var(--accent);text-transform:uppercase;margin-bottom:.9rem;opacity:.7;
}
.tc-title{font-family:'Cormorant Garamond',serif;font-size:1.35rem;font-weight:400;line-height:1.25;margin-bottom:.8rem}
.tc-preview{font-size:.86rem;line-height:1.75;color:var(--muted);font-weight:300;font-family:'Cormorant Garamond',serif;font-style:italic}
.tc-footer{display:flex;align-items:center;justify-content:space-between;margin-top:1.4rem}
.tc-author{font-family:'DM Mono',monospace;font-size:.58rem;color:var(--muted);letter-spacing:.08em}
.tc-read{font-family:'DM Mono',monospace;font-size:.58rem;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);opacity:0;transition:opacity .3s}
.thought-card:hover .tc-read{opacity:.7}

/* Thought modal */
.thought-overlay{
  display:none;position:fixed;inset:0;z-index:200;
  background:rgba(3,4,10,.97);backdrop-filter:blur(20px);
  align-items:flex-start;justify-content:center;
  padding:2rem 1.5rem;overflow-y:auto;
}
.thought-overlay.open{display:flex}
.thought-modal{
  width:min(740px,98vw);margin:auto;
  background:var(--surface);border:1px solid var(--border2);
  border-radius:4px;overflow:hidden;animation:modalIn .35s ease;
}
@keyframes modalIn{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
.tm-header{
  padding:2rem 2.5rem 1.8rem;border-bottom:1px solid var(--border);
  display:flex;align-items:flex-start;justify-content:space-between;gap:1.5rem;
}
.tm-cat{font-family:'DM Mono',monospace;font-size:.6rem;letter-spacing:.18em;text-transform:uppercase;color:var(--accent);margin-bottom:.6rem;opacity:.8}
.tm-title{font-family:'Cormorant Garamond',serif;font-size:clamp(1.6rem,4vw,2.4rem);font-weight:300;line-height:1.1}
.tm-close{background:none;border:none;color:var(--muted);cursor:pointer;font-size:1.2rem;padding:.3rem;flex-shrink:0;transition:color .3s;line-height:1}
.tm-close:hover{color:var(--text)}
.tm-body{padding:2.5rem;font-family:'Cormorant Garamond',serif;font-size:1.12rem;line-height:2;color:rgba(232,228,220,.82);white-space:pre-wrap}
.tm-footer{
  padding:1.2rem 2.5rem;border-top:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.8rem;
}
.tm-author{font-family:'DM Mono',monospace;font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.tm-date{font-family:'DM Mono',monospace;font-size:.58rem;letter-spacing:.08em;color:rgba(122,118,114,.4)}
.tm-leave{
  background:none;border:none;font-family:'DM Mono',monospace;
  font-size:.6rem;letter-spacing:.14em;text-transform:uppercase;
  color:var(--muted);cursor:pointer;transition:color .3s;padding:.3rem 0;
}
.tm-leave:hover{color:var(--accent)}

footer{
  position:relative;z-index:1;padding:3rem;border-top:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem;
}
.footer-logo{font-family:'Cormorant Garamond',serif;font-size:1.3rem;font-weight:300;letter-spacing:.1em;color:rgba(232,228,220,.25)}
.footer-tag{font-family:'DM Mono',monospace;font-size:.62rem;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}

::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px}
canvas{-webkit-tap-highlight-color:transparent}

@media(max-width:768px){
  nav{padding:.9rem 1.2rem}
  .nav-link{display:none}
  .thoughts-hero{padding:6rem 1.2rem 3rem}
  .thoughts-section{padding:3rem 1.2rem}
  .thoughts-grid{grid-template-columns:1fr}
  .thought-card{border-right:none}
  .tm-header{padding:1.4rem}
  .tm-body{padding:1.5rem 1.4rem}
  .tm-footer{padding:1rem 1.4rem;flex-direction:column;align-items:flex-start}
  footer{flex-direction:column;text-align:center;padding:2.5rem 1.2rem}
  .filter-bar{padding:2rem 1.2rem}
}
</style>
</head>
<body>
<canvas id="bg-canvas"></canvas>

<nav>
  <a class="logo" href="index.html">N<span>◦</span>ema</a>
  <div class="nav-right">
    <a class="nav-link" href="index.html">Home</a>
    <a class="nav-back" href="index.html">← Back to Noema</a>
  </div>
</nav>

<section class="thoughts-hero">
  <div class="hero-eyebrow">The living archive</div>
  <h1 class="hero-title">Thoughts that<br/><em>refuse to leave.</em></h1>
  <p class="hero-sub">A curated collection of philosophical fragments, realizations, and ideas placed here to be found.</p>
</section>

<div class="filter-bar">
  <span class="filter-label">Filter</span>
  <div class="filter-tags" id="filter-tags">
    <span class="filter-tag active" data-cat="all" onclick="filterThoughts(this,'all')">All</span>
  </div>
</div>

<section class="thoughts-section">
  <div class="thoughts-grid" id="thoughts-grid"></div>
</section>

<footer>
  <div class="footer-logo">N◦ema</div>
  <div class="footer-tag">A living universe of thought</div>
</footer>

<!-- Modal -->
<div class="thought-overlay" id="thought-overlay" onclick="if(event.target===this)closeModal()">
  <div class="thought-modal">
    <div class="tm-header">
      <div>
        <div class="tm-cat"  id="tm-cat"></div>
        <div class="tm-title" id="tm-title"></div>
      </div>
      <button class="tm-close" onclick="closeModal()">✕</button>
    </div>
    <div class="tm-body"   id="tm-body"></div>
    <div class="tm-footer">
      <div class="tm-author" id="tm-author"></div>
      <div class="tm-date"   id="tm-date"></div>
      <button class="tm-leave" onclick="closeModal()">Leave in silence</button>
    </div>
  </div>
</div>

<script>
const API_BASE = 'https://noema-backend-production-7d5e.up.railway.app';

// ── Background ────────────────────────────────────────────────
const bgC = document.getElementById('bg-canvas');
const bgX = bgC.getContext('2d');
let pts = [];
function resizeBg(){ bgC.width=innerWidth; bgC.height=innerHeight; }
resizeBg(); addEventListener('resize', resizeBg);
for(let i=0;i<100;i++) pts.push({
  x:Math.random()*innerWidth, y:Math.random()*innerHeight,
  r:Math.random()*1.1+.2,
  vx:(Math.random()-.5)*.12, vy:(Math.random()-.5)*.1,
  a:Math.random()*.4+.08
});
(function animBg(){
  bgX.clearRect(0,0,bgC.width,bgC.height);
  pts.forEach(p=>{
    p.x+=p.vx; p.y+=p.vy;
    if(p.x<0)p.x=innerWidth; if(p.x>innerWidth)p.x=0;
    if(p.y<0)p.y=innerHeight; if(p.y>innerHeight)p.y=0;
    bgX.beginPath(); bgX.arc(p.x,p.y,p.r,0,Math.PI*2);
    bgX.fillStyle=`rgba(200,169,126,${p.a})`; bgX.fill();
  });
  const t=Date.now()*.001;
  [[.2,.3,'rgba(139,181,200,.05)'],[.8,.6,'rgba(200,169,126,.04)'],[.5,.1,'rgba(160,130,200,.03)']].forEach(([fx,fy,c],i)=>{
    const x=bgC.width*fx+Math.sin(t*.4+i)*50;
    const y=bgC.height*fy+Math.cos(t*.3+i)*40;
    const g=bgX.createRadialGradient(x,y,0,x,y,200);
    g.addColorStop(0,c); g.addColorStop(1,'transparent');
    bgX.fillStyle=g; bgX.fillRect(0,0,bgC.width,bgC.height);
  });
  requestAnimationFrame(animBg);
})();

// ── Seed thoughts — always visible, never empty ───────────────
const SEEDS = [
  {
    id:'s0', category:'consciousness',
    title:'The Watcher Within',
    preview:'Who observes the observer? At the edge of introspection lies an infinite recursion — the eye that cannot see itself.',
    body:'Who observes the observer? At the edge of introspection lies an infinite recursion — the eye that cannot see itself yet shapes everything it touches.\n\nThe very act of trying to catch the self in observation reveals only more observer, never the ground. Consciousness studying itself is like a hand trying to grasp itself whole — always present, never held.\n\nPerhaps awareness is not something we have, but something we are. And perhaps that distinction — between having and being — is the oldest confusion there is.',
    author:'William · Noema', published:true, created_at: new Date().toISOString(), _seed:true
  },
  {
    id:'s1', category:'memory',
    title:'Palimpsest',
    preview:'Memory is not storage. It is constant rewriting — each recall leaves a new impression over the last, until the original is only its own ghost.',
    body:'Memory is not storage. It is constant rewriting — each recall leaves a new impression over the last, until the original is only its own ghost.\n\nWe remember not the event but the last time we remembered it. Every act of recollection is also an act of fiction — subtle, unconscious, sincere.\n\nThis is not a flaw in human cognition. It is the mechanism by which we survive. A perfectly accurate memory would be a prison. The softening of edges, the gentle drift of meaning — these are the mind\'s mercy toward itself.',
    author:'William · Noema', published:true, created_at: new Date().toISOString(), _seed:true
  },
  {
    id:'s2', category:'time',
    title:'Simultaneity of Grief',
    preview:'Past and present collapse in loss. The person grieving now is also the child who did not yet know grief was already on its way.',
    body:'Past and present collapse in loss. The person grieving now is also the child who did not yet know grief was already on its way.\n\nTime does not heal so much as it multiplies the selves available to carry the wound. The wound does not shrink — we grow around it, until the ratio shifts, until the wound is no longer the whole landscape.\n\nGrief is not linear. It is geological. Layers upon layers, each era of sorrow pressing down on the last, until what remains is both lighter and more dense than anything you could have imagined at the beginning.',
    author:'William · Noema', published:true, created_at: new Date().toISOString(), _seed:true
  },
  {
    id:'s3', category:'love',
    title:'Cartography of Attachment',
    preview:'To love is to memorize someone. Their particular weight of silence. A geography that becomes your own internal landscape.',
    body:'To love is to memorize someone. Their particular weight of silence. The geography of another person becomes your own internal landscape — and when they leave, you find yourself wandering a country that no longer exists outside yourself.\n\nThis is the strange mathematics of love: it makes two maps. One of the other person. One of yourself as seen through their eyes. And you carry both, whether you want to or not.\n\nAttachment is not weakness. It is the evidence that consciousness can reach beyond its own borders.',
    author:'William · Noema', published:true, created_at: new Date().toISOString(), _seed:true
  },
  {
    id:'s4', category:'existence',
    title:'The Permission of Being',
    preview:'Nobody asked to be here. And yet here we are, inventing reasons to stay, to build, to leave marks on a world that will outlast our reasons.',
    body:'Nobody asked to be here. And yet here we are, inventing reasons to stay, to build, to leave marks on a world that will outlast our reasons.\n\nThe uninvited nature of existence is not its tragedy — it is the beginning of all genuine choice. A guest who arrived without being summoned is the only guest truly free to leave, and therefore the only guest whose staying means something.\n\nWe do not choose to exist. But we choose, every day, what existence will mean.',
    author:'William · Noema', published:true, created_at: new Date().toISOString(), _seed:true
  },
  {
    id:'s5', category:'fear',
    title:'The Unnamed Fear',
    preview:'The fears that resist naming are the most sovereign. They do not require objects. They are the weather of the mind before the storm arrives.',
    body:'The fears that resist naming are the most sovereign. They do not require objects. They are the weather of the mind before the storm arrives.\n\nNamed fears can be approached, bargained with, sometimes defeated. But the unnamed ones — they are the atmosphere itself. You cannot fight the air.\n\nPerhaps the work is not to name them but to learn to breathe differently inside them. To discover that the fear was not a wall but a room, and that you have always had the capacity to live in difficult rooms.',
    author:'William · Noema', published:true, created_at: new Date().toISOString(), _seed:true
  },
  {
    id:'s6', category:'consciousness',
    title:'Language Before Thought',
    preview:'Does the word precede the thought, or does thought precede the word? Perhaps there are ideas that exist only in the silence between.',
    body:'Does the word precede the thought, or does thought precede the word? Perhaps there are ideas that exist only in the silence between.\n\nLanguage is not a transparent window onto reality. It is a room with particular dimensions — some thoughts fit perfectly, others must crouch, others cannot enter at all.\n\nEvery language therefore contains a different consciousness. And every person who learns a new language discovers that they were, before, a slightly smaller version of themselves.',
    author:'William · Noema', published:true, created_at: new Date().toISOString(), _seed:true
  },
  {
    id:'s7', category:'time',
    title:'The Weight of the Present',
    preview:'The present moment is the only real thing, yet it vanishes the moment you name it. We live permanently in a tense that does not exist.',
    body:'The present moment is the only real thing, yet it vanishes the moment you name it. We live permanently in a tense that does not exist.\n\nThe past is a story we carry. The future is a story we anticipate. But the present — the actual now — is so thin it cannot be inhabited, only passed through.\n\nAnd yet we feel it. We feel the weight of now pressing against us. Perhaps what we call the present is not a moment at all but a posture — a way of standing at the edge of what has already happened.',
    author:'William · Noema', published:true, created_at: new Date().toISOString(), _seed:true
  },
];

// ── Data ──────────────────────────────────────────────────────
let allThoughts  = [...SEEDS]; // starts with seeds, backend thoughts replace/add
let currentFilter = 'all';

// ── Load from backend — seeds stay visible until backend responds ─────────────
async function loadThoughts(){
  try{
    const r = await fetch(`${API_BASE}/thoughts`);
    if(!r.ok) return; // seeds remain — no error shown
    const data = await r.json();
    if(data && data.length > 0){
      // Backend has real thoughts — use them, keep any seeds that don't overlap
      allThoughts = data;
    }
    // If backend returns empty array, seeds remain — page never looks empty
    buildFilterTags(allThoughts);
    renderThoughts(currentFilter === 'all' ? allThoughts : allThoughts.filter(t=>t.category===currentFilter));
  }catch(e){
    // Network error — seeds already showing, do nothing
  }
}

function buildFilterTags(thoughts){
  const cats = ['all', ...new Set(thoughts.map(t=>t.category).filter(Boolean).sort())];
  const bar  = document.getElementById('filter-tags');
  bar.innerHTML = cats.map(cat=>`
    <span class="filter-tag${cat==='all'&&currentFilter==='all'?' active':cat===currentFilter?' active':''}"
      data-cat="${cat}" onclick="filterThoughts(this,'${cat}')">
      ${cat}
    </span>`).join('');
}

function filterThoughts(el, cat){
  currentFilter = cat;
  document.querySelectorAll('.filter-tag').forEach(t=>t.classList.remove('active'));
  el.classList.add('active');
  const filtered = cat === 'all' ? allThoughts : allThoughts.filter(t=>t.category===cat);
  renderThoughts(filtered);
}

function renderThoughts(thoughts){
  const grid = document.getElementById('thoughts-grid');
  if(!thoughts || thoughts.length === 0){
    grid.innerHTML = `<div style="grid-column:1/-1;padding:5rem 2rem;text-align:center;font-family:'Cormorant Garamond',serif;font-size:1.2rem;font-style:italic;color:rgba(232,228,220,.2)">No thoughts in this space yet.</div>`;
    return;
  }
  grid.innerHTML = thoughts.map((t,i) => `
    <div class="thought-card" onclick="openThought(${i})">
      <div class="tc-cat">${t.category}</div>
      <div class="tc-title">${t.title}</div>
      <div class="tc-preview">${t.preview}</div>
      <div class="tc-footer">
        <span class="tc-author">${t.author || 'William · Noema'}</span>
        <span class="tc-read">read in full ↗</span>
      </div>
    </div>`).join('');
}

// ── Modal ─────────────────────────────────────────────────────
function openThought(idx){
  const list = currentFilter === 'all' ? allThoughts : allThoughts.filter(t=>t.category===currentFilter);
  const t = list[idx];
  if(!t) return;
  document.getElementById('tm-cat').textContent    = t.category;
  document.getElementById('tm-title').textContent  = t.title;
  document.getElementById('tm-body').textContent   = t.body;
  document.getElementById('tm-author').textContent = t.author || 'William · Noema';
  document.getElementById('tm-date').textContent   = t._seed ? '' : t.created_at
    ? new Date(t.created_at).toLocaleDateString('en-US',{year:'numeric',month:'long',day:'numeric'})
    : '';
  document.getElementById('thought-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal(){
  document.getElementById('thought-overlay').classList.remove('open');
  document.body.style.overflow = '';
}

document.addEventListener('keydown', e=>{ if(e.key==='Escape') closeModal(); });

// ── Init — render seeds immediately, then try backend ─────────────────────────
buildFilterTags(SEEDS);
renderThoughts(SEEDS);
loadThoughts(); // replaces seeds if backend has content
</script>
</body>
</html>
