# 7. Pass selected goals through all layers as is

Date: 2022-03-05

## Status

Accepted

## Context

Historically, there was no consensus on a question how to manage selected goals in different logic layers.
On each layer, a custom desicion could be applied.
Nevertheless, this ascpect needs standartization.
As a number of layer grows, custom decisions start to interfere with wach other, causing strange bugs and test failures.

## Decision

We've decided to implement a standard here:

1. Every implementor of `Graph` interface **must** show selected goals (current and previous) together with filtered ones in its `q()` method.

2. Every implementor of `Graph` interface **should** change selectors in event handlers as little as possible.
Selection should not be changed without a very strong reason to do it.
This rule is not applied to `Goals` class itself, because it's the main manager of subgoals.

## Consequences

The most of the layers have already been modified to match these 2 rules.
The only exception is a `Zoom` class.
Currently, it actively tries to keep selection inside the zoomed area, by generating `Select` and `HoldSelect` events on need.
This behavior will be changed.

We expect the following positive impact:

* A code and logic of `Zoom` layer should become much simpler
* All layers should behave in the same way, without exceptions

We expect the following negative impact:

* Behavior changes in `Zoom` may cause several new application bugs.
We should thoroughly test this change to catch and/or prevent them.
