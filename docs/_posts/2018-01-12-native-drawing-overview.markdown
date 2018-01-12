---
layout: post
title:  "Native drawing overview"
date:   2018-01-12 23:32:15 +0500
tags: architecture notes
---

A bit of light must be shed on [long-running (endless?) feature "native rendering"][task_5].

SiebenApp was inspired mostly by GraphViz.
GraphViz uses [Sugiyama framework][sugiyama_framework] to draw graphs.
So, SiebenApp tries too.

This method consists of several steps.
Some of them are already implemented in SiebenApp, some not.

* [x] **Cycle removal**. At the very beginning we must remove all loops from graph, making it acyclic. Since SiebenApp allows to create only acyclic goal graphs by logical reasons, this step may be considered to be done automatically.
* [x] **Layer assignment**. Each vertex (goal) must be assigned to a level. This was implemented [quite recently][min_width_commit] using "Minimum width" algorithm. This algorithm restricts a number of goals assigned to a level, which makes it more suitable to the limited window width comparing to implementation in `dot`. With limited width you don't need to scroll window content left and right all the time. As a tradeoff, resulting graph has greater height and longer edges. I hope to improve this situation later.
* [ ] **Vertex ordering**. On each layer, goals are sorted in order to reduce edge intersections. This step is important because it greatly reduces chaos in graph. Currently, I'm fighting with this stage. I cannot consider [task][task_5] finished until I get some kind of goal sorting.
* [x] **Coordinate assignment**. After all, goals should be properly placed on a layer. In current implementation this is made by some kind of "hack". I just use `QGridLayout` to place goals in a row. This looks quite ugly but was easy to implement. Sometimes in future I'll have to fix this.

Currently, it looks like this:

![goals intersected with edges](/SiebenApp/images/2018-01-12-native/native_drawing.jpg)

As you can see, a number of edge-edge and edge-goal intersections is big.
This is the main reason why I haven't switched rendering to the native implementation yet.

**But!** Despite of its uglyness, it's already working on any desktop platform that supports Qt and doesn't require GraphViz.

So I hope, someone may find it interesting or even useful.
As for myself, I use it almost every day :)

[sugiyama_framework]: https://en.wikipedia.org/wiki/Layered_graph_drawing
[min_width_commit]: https://github.com/ahitrin/SiebenApp/commit/2d776dd286dbd44e563a4ff53b16d8823aeb3dbf
[task_5]: https://github.com/ahitrin/SiebenApp/issues/5
