# .NET application build and publish rules

Copy or merge this section into a .NET application's `AGENTS.md`. It is a behavioral engineering rule, not a Codex command-permission `.rules` file. It applies only to SDK-style .NET application development and delivery, not to non-.NET projects or NuGet package publication.

## .NET application build and publish rules

- Read the nearest `AGENTS.md`, product documentation, `global.json`, solution/project files, `Directory.Build.*`, NuGet configuration, publish profiles, and checked-in scripts before choosing commands.
- Treat each deliverable application as an ownership boundary. Build, test, and publish it through its product solution and repository-owned scripts; use a workspace solution only for explicitly required integration checks.
- Prefer checked-in build/test/publish scripts over reconstructed `dotnet` commands because they may establish native prerequisites, caches, output paths, and packaging layout.
- Keep `bin`, `obj`, test results, logs, caches, staging directories, and publish output under the owning product's ignored artifact tree. Do not scatter generated files beside source.
- Run restore/build, applicable tests, and publish in that order. Use `Release` for delivery unless the repository or user explicitly requires another configuration.
- Do not run commands concurrently when they write the same `obj`, cache, output, or fixed publish directory.
- Preserve the established target framework, runtime identifier, and framework-dependent/self-contained policy. Do not silently enable trimming, single-file, ReadyToRun, AOT, signing, obfuscation, or installer changes.
- For a fixed publish path, publish to a unique staging directory inside the artifact root, validate it, then replace the old directory transactionally. Preserve or restore the last known-good publish directory on failure.
- Validate the expected entry point, `.deps.json`/`.runtimeconfig.json` when applicable, native libraries, content/configuration files, and repository-defined dependency layout.
- Treat the complete publish directory as the deliverable unless a verified installer or packaging manifest defines otherwise; do not hand off only the EXE by assumption.
- Smoke-test the published application when safe: launch affected desktop views, exercise a bounded console/service path, or call a non-production health endpoint. Do not claim runtime success from compilation alone.
- Do not connect hardware, enable motion, mutate production data, change machine configuration, sign artifacts, or publish packages without the required explicit authorization.
- Record commands, results, warnings/tests, absolute artifact path, entry point, target framework, runtime identifier, deployment model, and every unperformed environment-specific validation boundary.
- Use the `build-publish-dotnet-app` Skill for the complete workflow and verification checklist.
