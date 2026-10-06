"""Local academic prototype: cybersecurity awareness and safe simulation.

Run with Python 3.11+: python source_code/app.py
Uses only Python's standard library and SQLite. Demo data is synthetic.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from pathlib import Path
import hashlib, hmac, html, secrets, sqlite3, time

DB = Path(__file__).resolve().parent / "prototype.sqlite3"
HOST, PORT = "127.0.0.1", 8000
USERS = [("employee@demo.local", "LearnerDemo26!", "employee"),
         ("manager@demo.local", "ManagerDemo26!", "manager"),
         ("admin@demo.local", "AdminDemo26!", "admin")]
COHORT = "Demo Cohort A"
SCENARIOS = {"shared_file": "Shared file notice", "password_reset": "Password reset notice", "invoice": "Invoice review request"}
LESSON = "Unexpected requests deserve a second look. Check the sender's full address, inspect links without opening them, and be cautious of urgency or requests for passwords and payment. Verify unusual requests through a known, separate channel. Use your organization's report process instead of replying."
QUESTIONS = [
 ("A message asks you to sign in through an unfamiliar link. What is the safest first step?", ["Open the link quickly", "Verify the request through a known channel", "Reply with your password"], 1),
 ("Which detail is useful when checking a sender?", ["The full email address and domain", "Only the display name", "The message color"], 0),
 ("What should you do with a suspicious message in this practice?", ["Forward it to friends", "Enter sample credentials", "Use the report control"], 2),
]

def score_answers(answers):
    """Validate one complete knowledge check and return its correct-answer count."""
    if len(answers) != len(QUESTIONS) or any(answer not in (0, 1, 2) for answer in answers):
        raise ValueError("Choose one valid answer for every question")
    return sum(answer == question[2] for answer, question in zip(answers, QUESTIONS))

def approved_scenario(scenario):
    return scenario in SCENARIOS

def valid_simulation_event(event):
    return event in ("reported", "clicked")

def dbopen():
    db = sqlite3.connect(DB, timeout=10); db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON"); return db

def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return salt.hex()+"$"+key.hex()

def password_matches(password, stored):
    try:
        salt, digest = stored.split("$")
        got = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 310_000).hex()
        return hmac.compare_digest(got, digest)
    except (ValueError, TypeError): return False

def initialize():
    d=dbopen(); d.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN ('employee','manager','admin')),cohort TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id),csrf TEXT NOT NULL,expires INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS lesson_completions(user_id INTEGER PRIMARY KEY REFERENCES users(id),lesson_version TEXT NOT NULL,completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS assessments(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id),score INTEGER NOT NULL,total INTEGER NOT NULL,submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS campaigns(id INTEGER PRIMARY KEY,scenario_key TEXT NOT NULL,cohort TEXT NOT NULL,created_by INTEGER NOT NULL REFERENCES users(id),created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,status TEXT NOT NULL DEFAULT 'Scheduled in local demo');
    CREATE TABLE IF NOT EXISTS simulation_events(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id),scenario_key TEXT NOT NULL,event_type TEXT NOT NULL CHECK(event_type IN ('reported','clicked')),occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS audit_events(id INTEGER PRIMARY KEY,actor_id INTEGER REFERENCES users(id),action TEXT NOT NULL,occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    """)
    for email,pw,role in USERS:
        if not d.execute("SELECT 1 FROM users WHERE email=?",(email,)).fetchone():
            d.execute("INSERT INTO users(email,password_hash,role,cohort) VALUES(?,?,?,?)",(email,hash_password(pw),role,COHORT))
    # Four synthetic participants make aggregate reporting meet its five-person minimum.
    for n in range(1,5):
        email=f"learner{n}@synthetic.demo"
        if not d.execute("SELECT 1 FROM users WHERE email=?",(email,)).fetchone():
            cur=d.execute("INSERT INTO users(email,password_hash,role,cohort) VALUES(?,?,?,?)",(email,hash_password(secrets.token_urlsafe(16)),"employee",COHORT))
            d.execute("INSERT INTO lesson_completions(user_id,lesson_version) VALUES(?,?)",(cur.lastrowid,"1.0"))
            d.execute("INSERT INTO assessments(user_id,score,total) VALUES(?,?,?)",(cur.lastrowid,2,3))
    seeds=[r[0] for r in d.execute("SELECT id FROM users WHERE email LIKE 'learner%@synthetic.demo'")]
    if seeds and not d.execute("SELECT 1 FROM simulation_events LIMIT 1").fetchone():
        for i,uid in enumerate(seeds): d.execute("INSERT INTO simulation_events(user_id,scenario_key,event_type) VALUES(?,?,?)",(uid,"shared_file","reported" if i<3 else "clicked"))
    d.commit(); d.close()

def e(x): return html.escape(str(x),quote=True)
def csrf_input(token): return f'<input type="hidden" name="csrf" value="{e(token)}">'

CSS="""<style>
:root{--ink:#16324f;--muted:#627487;--teal:#087e83;--line:#dbe5ea;--bg:#f4f7f9}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#1e2d3b;font:16px/1.55 'Segoe UI',Arial,sans-serif}.top{height:68px;padding:0 max(calc((100vw - 1080px)/2),24px);display:flex;align-items:center;justify-content:space-between;background:#fff;border-bottom:1px solid var(--line)}.brand{font-size:21px;font-weight:750;color:var(--ink);text-decoration:none}.brand span{font-size:13px;font-weight:500;color:var(--muted);margin-left:9px}.who{display:flex;align-items:center;gap:12px;color:var(--muted);font-size:14px}.who b,.pill{background:#e6f3f2;color:#136b6d;border-radius:20px;padding:4px 10px}.who b{font-size:12px}main{max-width:1000px;margin:34px auto;padding:0 24px}h1{color:var(--ink);font-size:30px;line-height:1.2;margin:0 0 8px}h2{color:var(--ink);font-size:20px;margin:0 0 10px}p{margin:8px 0;color:#526375}.eyebrow{font-size:12px;text-transform:uppercase;letter-spacing:.09em;color:var(--teal);font-weight:700;margin-bottom:7px}.lede{font-size:17px;color:var(--muted);margin:0 0 25px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card{background:white;border:1px solid var(--line);border-radius:14px;padding:22px;margin:0 0 18px;box-shadow:0 4px 18px #17324f08}.wide{grid-column:1/-1}.small{font-size:13px;color:var(--muted)}button,.button{background:var(--teal);border:0;color:white;font-weight:650;font-size:15px;border-radius:8px;padding:11px 16px;cursor:pointer;text-decoration:none;display:inline-block}button:hover,.button:hover{background:#086a6f}button.danger{background:#fff1ef;color:#99443e;border:1px solid #f0d2cf}.link{padding:0;background:none;color:var(--teal);font-size:14px}.inline{display:inline}label{display:block;font-size:13px;font-weight:650;margin:12px 0 5px;color:#425669}input[type=email],input[type=password],select{width:100%;border:1px solid #becdd5;border-radius:7px;padding:11px;background:#fff;font:inherit}input[type=radio]{accent-color:var(--teal)}.option{display:block;padding:9px 4px;color:#3e5060}.hero{background:#e8f4f4;border-left:4px solid var(--teal);border-radius:9px;padding:15px 17px;margin:14px 0}.success{color:#126b4d;background:#eaf7f0;border-radius:8px;padding:12px 14px;margin-top:12px}.warning{color:#81561a;background:#fff5de;border-radius:8px;padding:12px 14px;margin-top:12px}.message{border:1px solid #d8e3e9;background:#fbfcfd;border-radius:10px;padding:16px;margin:14px 0}.mailhead{font-size:13px;color:#627487;border-bottom:1px solid var(--line);padding-bottom:8px;margin-bottom:10px}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:14px 0}.metric{background:#f4f8fa;border-radius:10px;padding:14px}.metric strong{font-size:26px;color:var(--ink);display:block}.metric span{font-size:12px;color:var(--muted)}.row{display:flex;justify-content:space-between;align-items:center;gap:12px;border-top:1px solid var(--line);padding:12px 0}.notice{max-width:1000px;margin:18px auto 0;padding:12px 18px;background:#eaf7f0;color:#126b4d;border-radius:8px}.login{max-width:430px;margin:8vh auto}.demo-creds{font-size:13px;background:#f1f5f7;padding:13px;border-radius:8px;color:#43576a}.tagline{font-size:13px;color:#698092;margin-top:24px}.footer{border-top:1px solid var(--line);padding-top:16px;margin-top:22px;color:#728392;font-size:12px}@media(max-width:700px){.grid{grid-template-columns:1fr}.metrics{grid-template-columns:1fr 1fr}.top{padding:0 15px}main{padding:0 15px;margin-top:22px}}
</style>"""

def page(title,body,user=None,notice=""):
    nav=""
    if user:
        nav=f'<div class="top"><a class="brand" href="/">SafeSteps <span>Security learning</span></a><div class="who">{e(user["email"])} <b>{e(user["role"].title())}</b><form method="post" action="/logout" class="inline">{csrf_input(user["csrf"])}<button class="link">Sign out</button></form></div></div>'
    alert=f'<div class="notice">{e(notice)}</div>' if notice else ""
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)} | SafeSteps</title>{CSS}</head><body>{nav}{alert}<main>{body}<div class="footer">Academic prototype · Synthetic data · No live email is sent · Not for real phishing campaigns</div></main></body></html>'

class App(BaseHTTPRequestHandler):
    server_version="SafeStepsLocal/0.1"
    def log_message(self,fmt,*args): print(f"{self.log_date_time_string()} {self.address_string()} {fmt%args}")
    def send_html(self,body,status=200,cookie=None,clear=False):
        data=body.encode(); self.send_response(status); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(data)))
        for k,v in [("X-Content-Type-Options","nosniff"),("X-Frame-Options","DENY"),("Referrer-Policy","same-origin"),("Content-Security-Policy","default-src 'self' 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"),("Cache-Control","no-store")]: self.send_header(k,v)
        if cookie: self.send_header("Set-Cookie",f"sid={cookie}; HttpOnly; SameSite=Strict; Path=/; Max-Age=7200")
        if clear: self.send_header("Set-Cookie","sid=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0")
        self.end_headers(); self.wfile.write(data)
    def redirect(self,path):
        self.send_response(303); self.send_header("Location",path); self.send_header("Cache-Control","no-store"); self.end_headers()
    def form(self):
        n=min(int(self.headers.get("Content-Length","0")),20000); values=parse_qs(self.rfile.read(n).decode("utf-8","replace"),keep_blank_values=True); return {k:v[0] for k,v in values.items()}
    def user(self):
        sid=next((p.strip()[4:] for p in self.headers.get("Cookie","").split(";") if p.strip().startswith("sid=")),"")
        if not sid or len(sid)>100:return None
        d=dbopen(); row=d.execute("SELECT s.csrf,s.expires,u.id,u.email,u.role,u.cohort FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND u.active=1",(hashlib.sha256(sid.encode()).hexdigest(),)).fetchone()
        if not row or row["expires"]<int(time.time()):
            if row:d.execute("DELETE FROM sessions WHERE token_hash=?",(hashlib.sha256(sid.encode()).hexdigest(),));d.commit()
            d.close();return None
        result=dict(row);d.close();return result
    def need_user(self,roles=None):
        u=self.user()
        if not u:self.redirect("/login");return None
        if roles and u["role"] not in roles:self.send_html(page("Access denied",'<section class="card"><div class="eyebrow">403 · Permission check</div><h1>Access denied</h1><p>This role cannot open that view. Protected routes check role on the server.</p><a class="button" href="/">Return</a></section>',u),403);return None
        return u
    def csrf_ok(self,u,f):
        if not hmac.compare_digest(str(u["csrf"]),str(f.get("csrf",""))):self.send_html(page("Request rejected",'<section class="card"><h1>Request could not be verified</h1><p>Reload and try again.</p></section>'),403);return False
        return True
    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/login":
            body='''<section class="login"><div class="eyebrow">Small business security learning</div><h1>Practice safer email habits</h1><p class="lede">A local prototype for lessons, short assessments, and safe message-reporting practice.</p><div class="card"><h2>Sign in to the demo</h2><form method="post" action="/login"><label for="email">Email</label><input id="email" type="email" name="email" autocomplete="username" required><label for="password">Password</label><input id="password" type="password" name="password" autocomplete="current-password" required><p><button>Continue</button></p></form><div class="demo-creds"><b>Local demo accounts</b><br>Employee: employee@demo.local / LearnerDemo26!<br>Manager: manager@demo.local / ManagerDemo26!<br>Administrator: admin@demo.local / AdminDemo26!</div></div><p class="tagline">Development only. Synthetic records. No email is sent.</p></section>'''
            self.send_html(page("Sign in",body));return
        u=self.need_user()
        if not u:return
        if path=="/manager" and u["role"]!="manager": self.need_user(["manager"]);return
        if path=="/admin" and u["role"]!="admin": self.need_user(["admin"]);return
        if path=="/" and u["role"]=="employee":self.employee(u);return
        if path in ("/","/manager") and u["role"]=="manager":self.manager(u);return
        if path in ("/","/admin") and u["role"]=="admin":self.admin(u);return
        if path=="/health":self.send_html(page("Status",'<section class="card"><h1>Prototype is running</h1><p>Local server and SQLite store are active.</p></section>',u));return
        self.send_html(page("Not found",'<section class="card"><h1>Page not found</h1><a class="button" href="/">Return</a></section>',u),404)
    def do_POST(self):
        path=urlparse(self.path).path; f=self.form()
        if path=="/login":
            d=dbopen(); r=d.execute("SELECT id,password_hash FROM users WHERE email=? AND active=1",(f.get("email","").strip().lower(),)).fetchone()
            if not r or not password_matches(f.get("password",""),r["password_hash"]):
                d.close(); self.send_html(page("Sign in",'<section class="login"><div class="card"><h1>Sign in failed</h1><p>Check the demo credentials and try again.</p><a class="button" href="/login">Back</a></div></section>'),401);return
            sid=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(24)
            d.execute("INSERT INTO sessions(token_hash,user_id,csrf,expires) VALUES(?,?,?,?)",(hashlib.sha256(sid.encode()).hexdigest(),r["id"],csrf,int(time.time())+7200));d.execute("INSERT INTO audit_events(actor_id,action) VALUES(?,?)",(r["id"],"signed in"));d.commit();d.close()
            self.send_response(303);self.send_header("Location","/");self.send_header("Set-Cookie",f"sid={sid}; HttpOnly; SameSite=Strict; Path=/; Max-Age=7200");self.send_header("Cache-Control","no-store");self.end_headers();return
        u=self.user()
        if not u:self.redirect("/login");return
        if not self.csrf_ok(u,f):return
        d=dbopen()
        if path=="/logout":
            sid=next((p.strip()[4:] for p in self.headers.get("Cookie","").split(";") if p.strip().startswith("sid=")),"");d.execute("DELETE FROM sessions WHERE token_hash=?",(hashlib.sha256(sid.encode()).hexdigest(),));d.commit();d.close();self.send_response(303);self.send_header("Location","/login");self.send_header("Set-Cookie","sid=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0");self.end_headers();return
        if path=="/lesson/complete" and u["role"]=="employee":
            d.execute("INSERT OR REPLACE INTO lesson_completions(user_id,lesson_version) VALUES(?,?)",(u["id"],"1.0"));action="completed lesson version 1.0";dest="/?done=lesson"
        elif path=="/assessment/submit" and u["role"]=="employee":
            try: answers=[int(f.get(f"q{i}","-1")) for i in range(len(QUESTIONS))]
            except ValueError: answers=[]
            if len(answers)!=3 or any(a not in (0,1,2) for a in answers):d.close();self.send_html(page("Invalid response",'<section class="card"><h1>Choose an answer for every question</h1><a class="button" href="/">Return</a></section>',u),400);return
            try: score=score_answers(answers)
            except ValueError:d.close();self.send_html(page("Invalid response",'<section class="card"><h1>Choose an answer for every question</h1><a class="button" href="/">Return</a></section>',u),400);return
            d.execute("INSERT INTO assessments(user_id,score,total) VALUES(?,?,?)",(u["id"],score,len(QUESTIONS)));action="submitted knowledge check";dest=f"/?done=assessment&score={score}"
        elif path=="/simulation/event" and u["role"]=="employee":
            event=f.get("event_type","")
            if not valid_simulation_event(event):d.close();self.send_html(page("Invalid action",'<section class="card"><h1>Choose a practice action</h1></section>',u),400);return
            d.execute("INSERT INTO simulation_events(user_id,scenario_key,event_type) VALUES(?,?,?)",(u["id"],"shared_file",event));action="recorded safe simulation "+event+" event";dest="/?done="+event
        elif path=="/campaign/schedule" and u["role"]=="manager":
            scenario=f.get("scenario","")
            if not approved_scenario(scenario):d.close();self.send_html(page("Unavailable",'<section class="card"><h1>Choose an approved scenario</h1></section>',u),400);return
            d.execute("INSERT INTO campaigns(scenario_key,cohort,created_by) VALUES(?,?,?)",(scenario,u["cohort"],u["id"]));action="scheduled local practice scenario: "+SCENARIOS[scenario];dest="/manager?scheduled=1"
        else:d.close();self.send_html(page("Unavailable",'<section class="card"><h1>Action unavailable</h1></section>',u),403);return
        d.execute("INSERT INTO audit_events(actor_id,action) VALUES(?,?)",(u["id"],action));d.commit();d.close();self.redirect(dest)
    def employee(self,u):
        d=dbopen();done=d.execute("SELECT completed_at FROM lesson_completions WHERE user_id=?",(u["id"],)).fetchone();last=d.execute("SELECT score,total FROM assessments WHERE user_id=? ORDER BY id DESC LIMIT 1",(u["id"],)).fetchone();d.close()
        q=parse_qs(urlparse(self.path).query);state=q.get("done",[""])[0];feedback=""
        if state=="lesson":feedback='<div class="success">Lesson completion saved to the local learning record.</div>'
        elif state=="assessment":feedback=f'<div class="success">Knowledge check saved. Score: {e(q.get("score",["0"])[0])} / 3. Answers are available for review.</div>'
        elif state=="reported":feedback='<div class="success">Good choice. The report event is recorded. Check the sender, urgency, and unfamiliar links. This is synthetic practice. No email was sent.</div>'
        elif state=="clicked":feedback='<div class="warning">Practice feedback: the simulated click was recorded. Do not enter credentials. Verify the request and report suspicious messages.</div>'
        lesson=(f'<div class="success">Completed {e(done["completed_at"])} · lesson v1.0</div>' if done else f'<form method="post" action="/lesson/complete">{csrf_input(u["csrf"])}<button>Mark lesson complete</button></form>')
        qhtml=""
        for i,(prompt,opts,_) in enumerate(QUESTIONS):
            qhtml+=f'<fieldset style="border:0;border-top:1px solid #dbe5ea;padding:14px 0"><legend><b>{i+1}. {e(prompt)}</b></legend>'
            for j,opt in enumerate(opts):qhtml+=f'<label class="option"><input required type="radio" name="q{i}" value="{j}"> {e(opt)}</label>'
            qhtml+='</fieldset>'
        assessment=(f'<div class="success">Latest attempt: {last["score"]}/{last["total"]}. Only score and total are saved.</div>' if last else '')+f'<form method="post" action="/assessment/submit">{csrf_input(u["csrf"])}{qhtml}<button>Submit knowledge check</button></form>'
        body=f'''<div class="eyebrow">Employee portal · Demo Cohort A</div><h1>Welcome to your learning plan</h1><p class="lede">Short practice, clear feedback, and a safe way to report a suspicious message.</p>{feedback}<div class="grid"><section class="card"><div class="eyebrow">01 · Learning</div><h2>Pause, inspect, verify</h2><p>{e(LESSON)}</p>{lesson}</section><section class="card"><div class="eyebrow">02 · Knowledge check</div><h2>Three quick questions</h2><p class="small">Your score supports learning. It is not used for employment decisions.</p>{assessment}</section><section class="card wide" id="practice"><div class="eyebrow">03 · Controlled practice</div><h2>Sample message: Shared file notice</h2><div class="message"><div class="mailhead">From: File Services &lt;share-update@files-notice.example&gt; · Subject: Review this shared document today</div><p>A file was shared with you. Sign in from the button below to keep access. This message is synthetic and has no real link.</p></div><form method="post" action="/simulation/event">{csrf_input(u["csrf"])}<button name="event_type" value="reported">Report this practice message</button> <button class="danger" name="event_type" value="clicked">I clicked in the simulation</button></form><p class="small">Only the selected event type is recorded. No email is sent or credentials collected.</p></section></div>'''
        self.send_html(page("Learning plan",body,u))
    def manager(self,u):
        d=dbopen();size=d.execute("SELECT COUNT(*) FROM users WHERE role='employee' AND cohort=?",(u["cohort"],)).fetchone()[0];comp=d.execute("SELECT COUNT(*) FROM lesson_completions c JOIN users u ON u.id=c.user_id WHERE u.role='employee' AND u.cohort=?",(u["cohort"],)).fetchone()[0];a=d.execute("SELECT COUNT(*) n,COALESCE(AVG(score*1.0/total),0) avg FROM assessments a JOIN users u ON u.id=a.user_id WHERE u.role='employee' AND u.cohort=?",(u["cohort"],)).fetchone();ev=d.execute("SELECT event_type,COUNT(*) n FROM simulation_events s JOIN users u ON u.id=s.user_id WHERE u.role='employee' AND u.cohort=? GROUP BY event_type",(u["cohort"],)).fetchall();cs=d.execute("SELECT created_at,scenario_key,status FROM campaigns WHERE cohort=? ORDER BY id DESC LIMIT 4",(u["cohort"],)).fetchall();d.close();counts={r["event_type"]:r["n"] for r in ev};query=parse_qs(urlparse(self.path).query);notice='<div class="success">Scenario scheduled in the local demo. No email was sent.</div>' if query.get("scheduled") else ""
        rows="".join(f'<div class="row"><span>{e(SCENARIOS[r["scenario_key"]])}</span><span class="pill">{e(r["status"])}</span></div>' for r in cs) or '<p class="small">No scenarios scheduled.</p>';opts="".join(f'<option value="{k}">{e(v)}</option>' for k,v in SCENARIOS.items())
        body=f'''<div class="eyebrow">Manager portal · Authorized cohort view</div><h1>Learning and practice overview</h1><p class="lede">Aggregate results for {e(u["cohort"])}. Individual records are not shown.</p>{notice}<div class="hero"><b>Privacy boundary:</b> cohort reporting requires five or more synthetic participants. Seeded records are for demonstration only.</div><section class="card"><div class="eyebrow">Cohort summary · {size} synthetic learners</div><div class="metrics"><div class="metric"><strong>{comp}/{size}</strong><span>Lesson complete</span></div><div class="metric"><strong>{a["n"]}</strong><span>Assessment attempts</span></div><div class="metric"><strong>{round(a["avg"]*100)}%</strong><span>Average score</span></div><div class="metric"><strong>{counts.get('reported',0)} / {counts.get('clicked',0)}</strong><span>Reported / clicked events</span></div></div><p class="small">Click counts are learning signals only. Event records contain a type and time, never credentials or message text.</p></section><div class="grid"><section class="card"><div class="eyebrow">Controlled simulation module</div><h2>Schedule local practice</h2><p>Choose an approved scenario for the synthetic cohort.</p><form method="post" action="/campaign/schedule">{csrf_input(u["csrf"])}<label>Approved scenario</label><select name="scenario">{opts}</select><p><button>Schedule in local demo</button></p></form><p class="small">No provider connection, recipients, or outgoing mail.</p></section><section class="card"><div class="eyebrow">Campaign history</div><h2>Recent schedules</h2>{rows}</section></div>'''
        self.send_html(page("Manager overview",body,u))
    def admin(self,u):
        d=dbopen();people=d.execute("SELECT role,COUNT(*) n FROM users GROUP BY role ORDER BY role").fetchall();audits=d.execute("SELECT a.action,a.occurred_at,u.role FROM audit_events a LEFT JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT 12").fetchall();d.close()
        ps="".join(f'<div class="row"><span>{e(r["role"].title())}</span><b>{r["n"]}</b></div>' for r in people);ah="".join(f'<div class="row"><span>{e(r["action"])}<br><span class="small">{e(r["occurred_at"])}</span></span><span class="pill">{e(r["role"] or "system")}</span></div>' for r in audits)
        body=f'<div class="eyebrow">Administrator portal · Local prototype</div><h1>System administration</h1><p class="lede">Review demo account roles and security-relevant actions.</p><div class="grid"><section class="card"><div class="eyebrow">Identity module</div><h2>Accounts by role</h2>{ps}<p class="small">Passwords are stored as salted PBKDF2 hashes. All learner data is synthetic.</p></section><section class="card"><div class="eyebrow">Audit and data module</div><h2>Recent audit events</h2>{ah}</section></div>'
        self.send_html(page("Administration",body,u))

def main():
    initialize(); print(f"SafeSteps is running at http://{HOST}:{PORT}"); print("Synthetic accounts are shown on sign-in. No email is sent.")
    ThreadingHTTPServer((HOST,PORT),App).serve_forever()
if __name__=="__main__":main()
