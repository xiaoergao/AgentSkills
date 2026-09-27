---
name: organize-windows-desktop-web
description: Organize Windows WPF/WebView2 desktop projects that embed an ASP.NET Core backend, serve a Web frontend, and use local SQLite into source, scripts, temporary build outputs, and a copyable APP directory. Use for directory cleanup, preserving local data during relocation, and portable-folder delivery of this architecture. Do not apply this layout to standalone servers, pure Web, Electron/Tauri, embedded firmware, or other architectures without an explicit matching project decision.
---

# Organize a Windows Desktop + Web Project

Apply this architecture profile only after confirming the project uses a WPF/WebView2 shell, an in-process ASP.NET Core backend, Web assets and local SQLite, and the user wants a copyable application folder. .NET 10, Vue 3 and Windows x64 are one validated example, not an instruction to upgrade or retarget an unrelated project.

Read [the project rules](references/project-rules.md) when adopting or changing the directory layout. They can be adapted into the target repository's `AGENTS.md`.

## Workflow

1. Inventory entry points, root discovery, resource paths, SQLite/attachment paths, environment overrides, launch scripts, build outputs and current publish policy. Distinguish immutable program resources, user state, regenerable temporary files and historical evidence before moving anything.
2. Apply the chosen product boundary: `src` for maintained source, `scripts` for executable workflows, root `temp` for development and test output, `artifacts/app` for the complete runtime folder. Do not add a duplicate Release directory unless the project requires one. Preserve necessary archives separately.
3. Make the APP independent of the source checkout and working directory. For this profile, put `runtime`, `config`, and `database` directly under APP: runtime holds Web assets, migrations, contracts, logs and browser state; config holds templates and local settings; database holds SQLite, durable attachments and backups. Do not nest another `artifacts` or source tree inside APP. When migrating existing layouts, update callers and preserve old attachment/backup references through narrowly scoped compatibility resolution or verified data migration, with containment checks retained.
4. Close the application normally before moving its database or replacing binaries. Migrate local config/data/backups with collision checks and file hashes. Preserve ACLs where required. Never replace existing state with a fresh test database, expose credentials in output, or infer that `artifacts` contains only disposable files.
5. Redirect .NET intermediates, npm dependencies/cache, Web build staging, test databases, browser profiles, screenshots and reports into root `temp`. Update package locks, scripts and resource discovery for a source rename. If a source `node_modules` junction is needed, verify its target; cleanup must not follow it outside the intended tree.
6. Build and test with the repository's scripts. Publish to unique staging, validate, then update only program resources while preserving state and the previous working version on failure. Avoid concurrent writes to shared `obj` or publish directories.
7. Verify the copied APP from an unrelated directory with repository root/config environment overrides cleared. Test fresh initialization, existing-state preservation, restart, port/database-lock release and upgrade behavior appropriate to the change. Test data stays in `temp`; disable real device I/O in test copies. Report untested clean-machine prerequisites honestly.

## Delivery decisions

- A single EXE does not imply a standalone application. Web files, migrations and mutable state can remain external inside APP.
- Framework-dependent deployment needs the target .NET runtimes; self-contained deployment increases size and must be an explicit project choice. Self-contained .NET does not include WebView2. Identify whether the project uses installed Evergreen or a packaged Fixed Version runtime, including its licensing/update responsibilities; do not claim a clean-PC success based on a development machine.
- Preserve the established framework, RID, trimming, single-file and AOT policy unless the task authorizes changing it. For WPF/reflection-heavy applications, do not enable trimming merely to reduce file count.
- Copy the entire APP only after shutdown. SQLite WAL and business attachments belong to the data set; online copies use the application's consistent backup mechanism. Do not copy only the main `.db` while it is running.
- Keep device protocols, authentication, write permissions and backend lifetime semantics unchanged during directory work. Desktop login-free behavior from a particular project is not a reusable security default.

## Completion record

State the new source and temporary roots, the absolute EXE path, what is included in APP, remaining machine prerequisites, data-preservation checks and actual startup tests. For a rules-only change, validate links/frontmatter/scope without claiming a business application build. Commit or push only within the user's requested repository and authorization.
