# 3. DSL for creation and representation of goal trees

Date: 2017-05-14

## Status

Accepted

## Context

We have to work with a lot of goal tree examples during SiebenApp testing.
Current API allows only to create goaltree step-by-step.
It makes hard to point a border between test setup and test actions.

## Decision

Create a declarative [DSL][DSL] that allows to define a goal tree that "exists before test actions".
Use it in all unit tests.

## Consequences

Tests will became more readable and clean.

[DSL]: https://en.wikipedia.org/wiki/Domain-specific_language
