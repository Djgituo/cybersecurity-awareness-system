# SafeSteps Prototype

SafeSteps is the first local implementation of the Cybersecurity Awareness and Phishing Simulation System described in the architecture and technical report.

## Start the development environment

Requires Python 3.11 or newer. The prototype uses Python's standard library and SQLite, so no package installation is required.

From the repository root in PowerShell, run:

```powershell
python source_code/app.py
```

Open <http://127.0.0.1:8000>. The local server creates `source_code/prototype.sqlite3` and seeds synthetic accounts and a five-participant demo cohort. Stop the server and delete that database file to reset the demonstration.

| Role | Email | Password |
|---|---|---|
| Employee | `employee@demo.local` | `LearnerDemo26!` |
| Manager | `manager@demo.local` | `ManagerDemo26!` |
| Administrator | `admin@demo.local` | `AdminDemo26!` |

## Working flows

- Employee: sign in, complete the versioned lesson, submit a three-question knowledge check, and report or record a simulated click on a synthetic practice message.
- Manager: review cohort-level completion, assessment, and event summaries; schedule an allowlisted practice scenario for the local cohort.
- Administrator: review account counts by role and recent audit events.

The application checks roles on the server for protected actions. Forms use a per-session CSRF token. Login creates a random opaque cookie marked HttpOnly and SameSite=Strict, and sessions expire after two hours. Passwords are stored as salted PBKDF2 hashes. SQLite persists the accounts, sessions, learning, assessment, campaign, event, and audit records.

## Scope and safety

This is an academic local prototype, not a production service. Its scenarios have no live recipients or active links, it sends no email, and it never collects credentials or message bodies. Demo participants and their records are synthetic. The manager page suppresses individual learner records by showing only cohort totals for a cohort of at least five. The application is bound to localhost and should not be exposed to the public internet.

Production use would require HTTPS, deployment-managed secrets, MFA for privileged roles, policy and legal review, tested retention and backups, accessibility and security assessment, and a carefully isolated mail-test integration. The local development cookie omits the Secure attribute because the demo uses HTTP on localhost.

## Architecture fit

The prototype is one deployable application with clear identity and policy, learning, assessment, simulation-event, reporting, and audit/persistence boundaries. SQLite is the controlled prototype data store. This modular-monolith approach keeps setup simple while preserving the logical module boundaries in `../design/system_architecture.png` and the functional and nonfunctional requirements in `../documentation/Q1_Q2_System_Architecture_and_Version_Control.docx`.
