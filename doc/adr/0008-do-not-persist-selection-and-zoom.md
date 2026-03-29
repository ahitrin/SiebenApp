# 8. Do not persist selection and zoom state

Date: 2026-03-29

## Status

Approved

## Context

Persistent storage for goal selection has been existing since the very first versions of the product.
Later, a similar storage for Zoom state was added.
As it occurred with time, this approach has some rough edges:

* A simple exploration glance over a Sieben file could easily lead to changes in the file itself, even when nothing was changed in structure or content of goals.
  This may easily lead to file conflicts when they're stored in a git repository, for example.
* A need to consider selections and zooming adds unnecessary complexity to CLI tools (like `sieben-manage`).
  Again, manual changes of view in GUI affects output of such tools, which is not good.

It seems better to exclude selection and zoom state from the list of persistent layers.

## Decision

Convert both `Zoom` and `Selectable` layers from persistent layers into simple view layers:

* Add database migrations to remove corresponding data and structures once;
* Always start from default layer settings when opening a saved files (instead of reading it from this file):
  * `Selectable`: select a goal with the lowest ID;
  * `Zoom`: do not zoom at all;
* Migrate creation of these layers from `layers.persistent_layers` into `layers.view_layers`.

## Consequences

We expect some simplifications as a positive consequences of this change:

* Simpler unit tests (some of them, at least);
* Simpler and more predictable behavior of CLI tools;
* A lesser risk of file conflicts when files are synced via git or another tool.

In other hand, some negative consequences also may take place.
For example, it could be not that comfortable to work with large goal files.
But we could live with this.
