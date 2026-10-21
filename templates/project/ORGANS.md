# Organs Integration Contract

**Status:** Conditional integration baseline
**Governs:** How this project evaluates Organs when available; the actual Organs repository and installed implementation are authoritative.
**Last verified:** 2026-10-21

## Principle

Organs is shared runtime infrastructure external to this project. Use its published interfaces when a needed capability is available and appropriate. Do not copy its implementation into this project or create a competing local service without a demonstrated need.

## Discovery before integration

Before relying on Organs, inspect the current repository and installed implementation where authorized. Identify actual published contracts, capabilities, configuration, and failure behavior. Mark each dependency as required or optional, and record evidence in this project's architecture documentation.

Do not infer endpoints, ports, service names, or behavior from this template. Registry, BUS, memory, telemetry, and execution capabilities must be verified against the actual installation before use.

## Boundaries

Organs does not automatically become this project's domain database, source of truth, or epistemic authority. This project remains responsible for its domain logic, data, architecture, and decisions. Do not modify the Organs installation or shared configuration incidentally; shared infrastructure changes require separate authorization and verification.

If Organs is absent or unavailable, report the gap honestly. Do not silently introduce a competing implementation or claim the integration works.
