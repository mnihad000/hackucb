Make this repository portable so it still works after being moved to a different parent folder, assuming the internal repo structure stays the same.

Scope:
- Work in the current repo only.
- Do not change product behavior except where required for path portability.
- Do not rely on any current absolute path on disk.
- Do not assume the app will always be launched from the same working directory.

What to check and fix:

1. Backend path portability
- Inspect how config, `.env`, and the investigation SQLite database path are resolved.
- Make backend config resolve relative to the backend project directory or another stable repo-relative location, not only the process working directory.
- Ensure moving the repo to another folder does not cause the backend to miss `.env` or silently create the DB in the wrong directory.

2. Local environment artifacts
- Remove or neutralize checked-in path-bound artifacts that will break after moving folders, especially:
  - editor settings with absolute interpreter paths
  - checked-in virtualenv assumptions
  - any scripts/config that reference a machine-specific absolute path
- Prefer repo-relative config where possible.
- If a checked-in virtualenv is present and clearly non-portable, do not make runtime depend on it.

3. Frontend portability
- Verify the frontend does not depend on the current parent folder path.
- Keep Vite/TS path resolution working after a folder move.

4. Docs and developer ergonomics
- Replace broken absolute local file references in docs if they are meant to remain usable after a move.
- Keep documentation honest about how to start the app from a fresh location.

5. Verification
- Run the smallest relevant verification you can:
  - backend tests that cover config/repository behavior
  - frontend build if it is cheap
- If something cannot be verified, say exactly why.

Known likely issues in this repo:
- Backend settings load `.env` using a relative filename.
- Backend default DB path is a relative filename.
- The investigation repository is instantiated from those settings at import time.
- There are editor settings with absolute Python paths from another machine.
- There may be checked-in `.venv` artifacts that are not portable.
- Some docs may contain absolute local file links.

Acceptance criteria:
- The repo can be moved to another folder on the same machine without breaking because of hardcoded absolute paths.
- Starting the backend from a reasonable location still finds the intended `.env` and DB path.
- The frontend still builds.
- Any remaining non-portable artifacts are either removed from the critical path or explicitly documented.

Output requirements:
- Implement the fixes directly.
- Summarize what changed.
- Call out any residual risks.
- Include exact file references in the final report.
