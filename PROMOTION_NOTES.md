Parallel Promotion Notes
------------------------

- Feature flag location: `charts/global-values.yaml` (enableParallelPromotion)
- Code-level guard: promotion orchestration checks `ENABLE_PARALLEL_PROMOTION` env var
- Sprint 3: feature remains disabled by default; enable only after full mesh validation
- Testing plan: enable in CI sandbox via Helm override and run parallel promotion smoke tests
