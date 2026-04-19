# Engineering Standards & Guidelines

To achieve our 5-year, 50-Phase roadmap of becoming the ultimate enterprise AI data fabric, Aether's development must stringently adhere to our established engineering culture. 

## 1. Test-Driven Development (TDD)
We follow a 0-regression tolerance policy. Tests are a first-class citizen of this repository, not an afterthought.

- **Write tests FIRST:** Before scaffolding your Rust implementation, write the mock expectations, the unit tests, and the integration endpoints.
- **Coverage Minimums:** No crate or UI package may be merged if the unit test coverage falls below 90%.
- **Rust Testing Tools:** 
  - Standard `cargo test` for unit logic.
  - `rstest` for parameterized data-driven tests.
  - `proptest` for fuzzing edge logic (crucial for PII boundaries).
- **TypeScript/UI Testing Tools:**
  - `Vitest` for Headless unit testing.
  - `Playwright` for E2E user-flow simulations.

> [!WARNING]
> Pre-commit hooks will automatically execute tests. Bypassing tests locally with `--no-verify` is strictly prohibited.

## 2. SOLID Principles
Our entire architecture relies on modular decoupling. 
- **Single Responsibility Principle (SRP):** Functions, files, and modules must do one thing. If an `EventFlattener` is flattening JSON, it MUST NOT also be serializing to Avro. Split it.
- **Open/Closed Principle:** Create designs (Traits in Rust, Interfaces in TS) that are easily extended. DO NOT continuously modify core implementations to bolt on new features.
- **Liskov Substitution:** Sub-modules and implementations must always fit seamlessly into the base abstractions.
- **Interface Segregation:** Create small, targeted Traits. A single massive `Database` trait is an anti-pattern. Split into `VectorReader`, `GraphWriter`, etc.
- **Dependency Inversion:** High-level modules should depend on abstractions, never on concrete implementations like `pgvector` or `Qdrant` directly.

## 3. Pull Request Protocol
- Prefix your PR bounds correctly (e.g., `feat(refinery): ...`, `test(shield): ...`).
- You MUST reference the relevant `docs/phases/Phase-X.md` in your PR to track velocity.
- CI/CD will fail your branch if `clippy`, `rustfmt`, `eslint`, or `prettier` emit any warnings. Fix them locally.
