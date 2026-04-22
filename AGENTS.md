# Codex Workflow Rules

Before making ANY changes:

1. Read context.md
2. Review all relevant .md files
3. Run: git status

## Required workflow

For every change:

1. Create checkpoint:
   git add .
   git commit -m "checkpoint before change"

2. Make changes

3. Verify:
   - code runs
   - no obvious errors

4. Commit:
   git add .
   git commit -m "<clear description of change>"

5. Push:
   git push origin main

## Rules

- Always commit before and after changes
- Always push after successful commit
- If push fails, report error and stop
- Do NOT skip steps
- Treat `app.py` as the primary app unless explicitly told otherwise
- Do not overwrite `app_reconstructed.py` unless explicitly asked
- Do not remove working functionality without approval
