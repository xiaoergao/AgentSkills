---
name: build-publish-dotnet-app
description: Build, test, publish, and verify SDK-style .NET applications through repository-owned solutions and scripts while keeping generated artifacts out of source trees. Use for .NET, C#, WPF, WinForms, console, worker, or ASP.NET application delivery; Release build failures; runtime identifier or self-contained decisions; publish-folder design; native dependency packaging; and reproducible release evidence. Do not use for non-.NET applications or NuGet package publishing.
---

# Build and Publish a .NET App

Treat the repository as the authority for product boundaries, commands, target frameworks, runtimes, and artifact locations. Prefer its checked-in build, test, and publish scripts over reconstructed `dotnet` commands.

## Workflow

1. Inspect before running commands.
   - Read the nearest `AGENTS.md`, product documentation, solution/project files, `global.json`, `Directory.Build.*`, NuGet configuration, publish profiles, and repository-owned scripts.
   - Identify the deliverable product, entry project, owning solution, target framework, runtime identifier, configuration, native prerequisites, and expected artifact directory.
   - Check `git status` and preserve unrelated changes.
2. Select one product boundary.
   - Use the product solution or product script for a deliverable. Use a workspace solution only when repository guidance defines it as the delivery entry point or when an integration check is explicitly required.
   - Do not build or publish an unrelated product merely because it shares the workspace.
3. Keep outputs isolated.
   - Send publish output, test results, logs, temporary staging directories, and caches to the owning product's ignored artifact tree.
   - Do not create ad hoc projects, `bin`, `obj`, publish folders, or test results beside source files.
4. Execute the repository pipeline in order.
   - Run the repository-owned build script first when it restores dependencies or builds native prerequisites.
   - Run focused tests, then the owning solution's applicable test gate.
   - Publish in `Release` unless the repository or user explicitly requires another configuration.
   - Avoid concurrent commands that write the same `obj`, output, cache, or fixed publish directory.
5. Publish transactionally when replacing a fixed delivery directory.
   - Publish to a unique staging directory under the artifact root.
   - Validate the staged entry point and required managed/native dependencies.
   - Check whether the current delivery directory is replaceable, retain it until staging passes, then swap directories and restore the prior directory if replacement fails.
   - Delete only verified generated directories contained by the intended artifact root.
6. Verify the deliverable.
   - Read [references/publish-verification.md](references/publish-verification.md) and apply the relevant checks.
   - Launch desktop applications or run service/console smoke checks when safe and supported. Do not substitute a successful compile for runtime verification.
7. Report evidence and limits.
   - State exact commands, exit status, warning/test counts, artifact path, entry point, deployment model, runtime identifier, and verification performed.
   - Record skipped hardware, UI, network, database, signing, installer, or production-environment validation without claiming it passed.

## Delivery Decisions

- Preserve the repository's existing framework-dependent or self-contained policy. If no policy exists, ask or explain the tradeoff before changing the deployment model.
- Pass a runtime identifier only when the application or native dependency is platform-specific or the requested deliverable requires it.
- Deliver the complete publish directory unless a verified installer or packaging step defines a different unit. Never assume copying only the executable is sufficient.
- Keep native libraries and content files in their repository-defined relative locations and verify they were copied.
- Do not silently change trimming, single-file, ReadyToRun, AOT, signing, obfuscation, versioning, or installer settings to make a publish command succeed.
- Do not use `--no-restore` or `--no-build` unless the prerequisite phase ran successfully with matching inputs and configuration.

## Failure Handling

- Stop at the first failed gate and preserve the last known-good fixed publish directory.
- Diagnose the first actionable error rather than hiding failures with warning suppression, broad exclusions, or dependency downgrades.
- Distinguish source errors, SDK/workload absence, restore/feed failure, locked files, native-toolchain failure, test failure, and packaging-layout failure.
- Do not delete broad cache or artifact roots as a default fix. If cleanup is necessary, resolve and validate the exact generated target first.

## Required Outcome

Leave the repository source tree clean of generated output and provide a concise delivery record. If source changes were requested, run the focused tests and owning Release build before handoff; if only a build was requested, do not modify source merely to manufacture success.
