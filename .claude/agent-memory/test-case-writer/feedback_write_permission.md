---
name: write-permission-required
description: Write tool permission is not pre-granted — test files must be approved before creation
metadata:
  type: feedback
---

Write tool access is not automatically granted. When writing test files for the first time in a session, the user must explicitly approve the Write permission before files can be created.

**Why:** Standard Claude Code sandbox policy — Write is a destructive tool and requires per-session approval.

**How to apply:** When authoring test files, present the full file content inline as code blocks so the user can review and approve, then request Write permission to materialize them. Do not assume Write is available just because Read and Grep worked.
