# .NET publish verification

Use only the checks relevant to the application's delivery model.

## Build and test evidence

- Confirm the selected SDK using `dotnet --info` or a pinned `global.json` when SDK selection matters.
- Confirm restore, Release build, and applicable tests completed with nonzero failures treated as failures.
- Capture warnings separately; compare with the repository's warning policy instead of reporting only the exit code.
- Confirm the command targeted the owning solution/project and the intended configuration and target framework.

## Publish layout

- Confirm the expected executable, app host, or primary DLL exists and is nonempty.
- Confirm `.deps.json` and `.runtimeconfig.json` are present when the deployment model needs them.
- Confirm required configuration/content files and native libraries are present at the relative paths the application resolves at runtime.
- Inspect unexpected root-level DLLs or duplicate dependency trees when the repository defines a constrained layout.
- Treat the full publish directory as the delivery unit unless an installer or package manifest proves otherwise.

## Deployment model

- Framework-dependent: record the required .NET/.NET Desktop/ASP.NET Core runtime and architecture.
- Self-contained: verify the target runtime identifier and that the runtime files are included.
- Single-file, trimming, ReadyToRun, or AOT: verify only when configured intentionally; these modes can change reflection, dynamic loading, native extraction, startup, and size behavior.
- Platform-specific/native application: test on the intended operating system and architecture; compilation alone does not prove loadability.

## Runtime smoke check

- Desktop UI: launch the published executable, inspect startup and affected views, then close it cleanly. Record when an interactive desktop is unavailable.
- Console/worker/service: exercise a safe help, version, health, or bounded startup/shutdown path.
- Web app: start with non-production settings, wait for readiness, call a health or minimal endpoint, then stop the process.
- Hardware or external-service application: verify a documented offline/simulation path when available. Do not connect, enable motion, mutate production data, or change machine configuration without explicit authorization.
- Check for missing-runtime, missing-native-library, configuration, binding, and startup exceptions.

## Reproducibility and handoff

- Report the absolute artifact directory and entry point.
- Record configuration, target framework, runtime identifier, deployment model, and command/script used.
- Record file size and SHA-256 for the primary deliverable when integrity tracking is useful.
- Confirm generated outputs remain ignored and outside source directories.
- List every unperformed environment-specific check as a remaining validation boundary.
