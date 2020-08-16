# 2. Create adaptive goal tree enumeration

Date: 2017-03-05

## Status

Accepted

## Context

Currently, we have a fixed mapping between the inner goal identificator (actually, just an index in `Goals.goals` dictionary) and the user-visible goal number that is used for selecion (also called "enumeration"). This decision was easy to implement, but it seems to have significant downsides.

1. Goal numbers can only grow and grow. This makes long-living trees look ugly. We may have only few open goals in a tree, but most of them could have 3-digit numbers (because of a big amount of closed goals which are also used to generate enumeration).
2. It makes difficult to create nested goaltrees (see issue #6). It seems reasonably for the nested goaltree to have its own enumeration starting from 1. But the current enumeration function is not flexible enough to support this naturally.

## Decision

We decide to extract the enumeration function `id_mapping` out from the `Goals` class. It should be transformed into the wrapper which transforms actual goal identificators into user-visible numbers and, respectively, keeps backward mapping (which is used for goal selection).

## Consequences

We expect following consequences for user interface:

1. Visible goal numbers may change significantly when user closes or deletes some of them, or changes view. We hope it will not be disappointing.
2. Own enumeration for nested goaltrees should now look naturally.
3. No "hidden selection" will be allowed (currently it's possible to select invisible goals because enumeration is global).

and for the code structure:

1. Field `selection_cache` may be also moved into the new `Enumeration` class.
2. Class `Goals` should become smaller and easier for testing.
3. **But** all existing tests that rely on current enumeration function must be refactored.
