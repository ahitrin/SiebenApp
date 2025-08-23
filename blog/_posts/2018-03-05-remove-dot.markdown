---
layout: post
title:  "Dot usage has been removed"
date:   2018-03-05
tags: rendering
---

Good news everyone!

At last it had happened: [issue #5][issue_5] is closed.
We have been relying on `dot` for a long time, but now it's time to take full control over rendering algorithms used in the application.
This is the only one possible way to tweak and tune it corresponding to our needs.

In addition, two important roads are open now:

 * **Simplified installation**. Now we don't have to either setup dependency on Graphviz nor pack it along with the application. It depends on Python and Qt5 only.
 * **Rich UI**. An old version of application was de-facto just an image viewer for Graphviz. We had no possibilities to manipulate goals using point-and-click user interface. Now this wall is ruined, and we're able to improve user interface in this direction.

Major changes in these directions are planned for the new version.
Development will be started as long as I've finished [this final issue][issue_11].

[issue_5]: https://github.com/ahitrin/SiebenApp/issues/5
[issue_11]: https://github.com/ahitrin/SiebenApp/issues/11
