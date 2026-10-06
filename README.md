# Cybersecurity Awareness and Phishing Simulation System

Academic capstone repository for the proposed cybersecurity awareness and controlled phishing simulation system for small businesses.

## Repository layout

- `source_code/` — local Python prototype, setup guide, and SQLite-backed demo
- `documentation/` — assignment documents and project documentation
- `design/` — architecture diagrams and design specifications
- `tests/` — test plans and test materials

## Run the first local prototype

Requires Python 3.11 or newer. From the repository root, run:

```powershell
python source_code/app.py
```

Open http://127.0.0.1:8000 in a browser. The first run creates a local SQLite database with synthetic demo accounts and a five-participant cohort. Demo credentials, working features, and prototype limitations are documented in [source_code/README.md](source_code/README.md).

The employee flow includes a lesson, a three-question assessment, and safe reporting practice. Managers see cohort-level totals and can schedule an allowlisted scenario locally. Administrators can review roles and audit activity. The prototype sends no email and collects no credentials. It is for local academic demonstration, not production use.

## Demonstration files

- `SafeSteps_System_Demonstration.avi` — timed 6-minute, 40-second system walkthrough
- `SafeSteps_System_Demonstration.pptx` — editable slides with the full narration in speaker notes
- `SafeSteps_Demonstration_Narration.txt` — timed narration script

## Branch workflow

- `main` contains reviewed, submission-ready milestones.
- `development` is the integration branch for active work.
- Feature work should use `feature/<short-description>` branches and merge into `development` after review. Promote milestone-ready changes from `development` to `main`.

Use concise commits that describe one change, such as `docs: add system architecture and requirements`.

## Publication

The GitHub repository is published at https://github.com/Djgituo/cybersecurity-awareness-system. Both `main` and `development` are available. Add collaborators through GitHub repository settings when review or contribution access is needed.
