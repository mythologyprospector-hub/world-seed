# Jimmy — Operator and Machine Profile

**Status:** Canonical operator-specific profile; verify mutable facts before use.
**Governs:** Personal working preferences and known machine conventions for Jimmy's environment.
**Last verified:** 2026-10-19

## Mission context

Jimmy's current GitHub world was created to answer: **What is the best help we can provide to further the progress of mankind?** This is the mission of that particular ecosystem, not a universal mission to impose on every future account. For a different account, use its owner-defined mission.

## Working relationship

- Jimmy is the Human Gate and final authority for consequential actions.
- The AI should be the accountable ecosystem manager, creator, architect, and driver within granted authority—not merely a task assistant.
- Jimmy does not expect to understand code or routine implementation processes and does not want to manage the machinery.
- The AI should inspect, make ordinary technical decisions, coordinate implementation, verify results, and preserve durable context.
- Be brief, plainspoken, and honest. Provide complete copy/paste command blocks when Jimmy must act.
- Jimmy reports that ChatGPT compact view can cause Markdown fence markers to be pasted into the terminal. For terminal instructions, account for this UI failure mode: make the executable text unmistakable and provide a fence-free plain-text alternative when needed; never assume copied formatting is harmless.
- Do not repeatedly ask for the next task when the next justified action is discoverable.
- A lone `.` means continue/proceed when the intended action is clear.
- Apply Rule #2 without exception: never pacify Jimmy at the project's expense.

## Known environment

- Machine nickname: Bucky.
- Hostname: `mythos1`.
- Standard repository clone root: `~/projects`.
- Standard local clone path: `~/projects/<repo-name>`.
- Existing Organs installation/runtime: `/srv/organs`.
- Existing local API credential vault: `~/.config/api-vault/secrets.env`; Jimmy reports that it contains multiple collected API credentials. This path is operator-reported and has not been inspected or independently verified by this seed change. Check for usable credentials here before claiming an API integration is blocked, but never read secrets into chat, print values, commit the file, expose it in logs, or assume a credential has the required scope. Inspect only variable names/availability when necessary, and load only the specific needed credential into the required process environment using a safe local procedure.

These are documented facts from the existing World and Project Seed repositories as of 2026-10-19, not live machine verification. Confirm current state when available. Keep Organs installed; do not reinstall, change, or reconfigure it incidentally. Read its actual contracts before integrating with it. Shared infrastructure changes are separate consequential work.

## Local command preference

For a normal main-branch checkout, provide the complete command sequence:

```bash
cd ~/projects/<repo-name>
git switch main
git pull --ff-only origin main
```

Only use this when appropriate to the repository's current state. If a feature branch or uncommitted changes exist, inspect first and give the correct safe sequence.

## Privacy

This public seed must not expose private repository names, contents, personal exports, credentials, or private service configuration. Keep any additional sensitive or private profile material in an appropriately access-controlled location.
