# coding: utf-8
import sqlite3
from html import escape
from os import path
from typing import Callable, List, Dict, Set

from siebenapp.domain import EdgeType, Graph
from siebenapp.enumeration import Enumeration
from siebenapp.goaltree import Goals, GoalsData, EdgesData, OptionsData
from siebenapp.layers import wrap_with_views
from siebenapp.zoom import Zoom

MIGRATIONS = [
    # 0
    [
        "create table migrations (version integer)",
        "insert into migrations values (-1)",
    ],
    # 1
    [
        """create table goals (
            goal_id integer primary key,
            name string,
            open boolean
        )""",
        """create table edges (
            parent integer,
            child integer,
            foreign key(parent) references goals(goal_id),
            foreign key(child) references goals(goal_id)
        )""",
        """create table selection (
            name string,
            goal integer,
            foreign key(goal) references goals(goal_id)
        )""",
    ],
    # 2
    [
        # change type of goals.name: string -> text
        """alter table goals rename to old_goals""",
        """create table goals (
            goal_id integer primary key,
            name text,
            open boolean
        )""",
        """insert into goals (goal_id, name, open)
           select goal_id, name, open from old_goals""",
        """drop table old_goals""",
        # change type of selection.name: string -> text
        """alter table selection rename to old_selection""",
        """create table selection (
            name text,
            goal integer,
            foreign key(goal) references goals(goal_id)
        )""",
        """insert into selection (name, goal)
           select name, goal from old_selection""",
        """drop table old_selection""",
    ],
    # 3
    [
        "alter table selection rename to settings",
    ],
    # 4
    [
        "alter table edges add column reltype integer not null default 1",
    ],
    # 5
    [
        """create table zoom (
            level integer primary key,
            goal integer,
            foreign key(goal) references goals(goal_id)
        )""",
        """insert into zoom (level, goal) select 1, 1 from settings
           where name = 'zoom' """,
        """insert into zoom (level, goal) select 2, goal from settings
           where name = 'zoom' and goal <> 1""",
        "delete from settings where name = 'zoom'",
    ],
    # 6
    [
        """create table new_edges (
            parent integer not null,
            child integer not null,
            reltype integer not null default 1,
            primary key(parent, child),
            foreign key(parent) references goals(goal_id),
            foreign key(child) references goals(goal_id)
        )""",
        "insert into new_edges select parent, child, 1 from edges",
        """insert or replace into new_edges
        select min(parent), child, 2 from edges where reltype=2 group by child""",
        "delete from edges",
        "insert into edges select * from new_edges",
    ],
    # 7
    [
        "drop table new_edges",
    ],
]


def save(goals: Graph, filename: str) -> None:
    if path.isfile(filename):
        connection = sqlite3.connect(filename)
        run_migrations(connection)
        save_updates(goals, connection)
    else:
        connection = sqlite3.connect(filename)
        run_migrations(connection)
        root_goals = goals
        while not isinstance(root_goals, Goals):
            root_goals = root_goals.goaltree
        goals_export, edges_export, select_export = Goals.export(root_goals)
        zoom_goals = goals
        while not isinstance(zoom_goals, Zoom):
            zoom_goals = zoom_goals.goaltree
        zoom_export = Zoom.export(zoom_goals)
        cur = connection.cursor()
        cur.executemany("insert into goals values (?,?,?)", goals_export)
        cur.executemany("insert into edges values (?,?,?)", edges_export)
        cur.executemany("insert into settings values (?,?)", select_export)
        cur.executemany("insert into zoom values (?, ?)", zoom_export)
        root_goals._events.clear()
        connection.commit()

    connection.close()


def save_updates(goals: Graph, connection: sqlite3.Connection) -> None:
    actions = {
        "add": ["insert into goals values (?,?,?)"],
        "toggle_close": ["update goals set open=? where goal_id=?"],
        "rename": ["update goals set name=? where goal_id=?"],
        "link": ["insert into edges values (?,?,?)"],
        "unlink": ["delete from edges where parent=? and child=? and reltype=?"],
        "select": [
            'delete from settings where name="selection"',
            'insert into settings values ("selection", ?)',
        ],
        "hold_select": [
            'delete from settings where name="previous_selection"',
            'insert into settings values ("previous_selection", ?)',
        ],
        "delete": [
            "delete from goals where goal_id=?",
            "delete from edges where child=?",
            "delete from edges where parent=?",
        ],
        "zoom": ["insert into zoom values (?, ?)"],
        "unzoom": ["delete from zoom where goal=?"],
    }
    cur = connection.cursor()
    while goals.events():
        event = goals.events().popleft()
        if event[0] in actions:
            for query in actions[event[0]]:
                if "?" in query:
                    cur.execute(query, event[1:])
                else:
                    cur.execute(query)
    connection.commit()


def load(filename: str, message_fn: Callable[[str], None] = None) -> Enumeration:
    if path.isfile(filename):
        connection = sqlite3.connect(filename)
        run_migrations(connection)
        cur = connection.cursor()
        names = list(cur.execute("select * from goals"))
        edges = list(cur.execute("select parent, child, reltype from edges"))
        settings = list(cur.execute("select * from settings"))
        zoom_data = list(cur.execute("select * from zoom"))
        cur.close()
        goals = Goals.build(names, edges, settings, message_fn)
        zoom = Zoom.build(goals, zoom_data)
    else:
        goals = Goals("Rename me", message_fn)
        zoom = Zoom(goals)
    return Enumeration(wrap_with_views(zoom))


def run_migrations(
    conn: sqlite3.Connection, migrations: List[List[str]] = None
) -> None:
    if migrations is None:
        migrations = MIGRATIONS
    cur = conn.cursor()
    try:
        cur.execute("select version from migrations")
        current_version = cur.fetchone()[0]
    except sqlite3.OperationalError:
        current_version = -1
    for num, migration in list(enumerate(migrations))[current_version + 1 :]:
        for query in migration:
            cur.execute(query)
        cur.execute("update migrations set version=?", (num,))
        conn.commit()


def split_long(line: str) -> str:
    margin = 20
    parts = []
    space_position = line.find(" ", margin)
    while space_position > 0:
        part, line = line[:space_position], line[(space_position + 1) :]
        parts.append(part)
        space_position = line.find(" ", margin)
    parts.append(line)
    return "\n".join(parts)


def _format_name(num: int, goal: Dict[str, str]) -> str:
    goal_name = escape(goal["name"])
    label = f'"{num}: {goal_name}"' if num >= 0 else f'"{goal_name}"'
    return split_long(label)


def dot_export(goals):
    data = goals.q(keys="open,name,edge,switchable")
    lines = []
    for num in sorted(data.keys()):
        goal = data[num]
        style = None
        if goal["switchable"] and goal["open"]:
            style = "bold"
        attributes = {
            "label": _format_name(num, goal),
            "color": "red" if goal["open"] else "green",
        }
        if style is not None:
            attributes["style"] = style
        attributes_str = ", ".join(
            f"{k}={attributes[k]}"
            for k in ["label", "color", "style", "fillcolor"]
            if k in attributes and attributes[k]
        )
        lines.append(f"{num} [{attributes_str}];")
    for num in sorted(data.keys()):
        for edge in data[num]["edge"]:
            color = "black" if data[edge[0]]["open"] else "gray"
            line_attrs = f"color={color}"
            if edge[1] == EdgeType.BLOCKER:
                line_attrs += ", style=dashed"
            lines.append(f"{edge[0]} -> {num} [{line_attrs}];")
    body = "\n".join(lines)
    return f"digraph g {{\nnode [shape=box];\n{body}\n}}"


def extract_subtree(source_goals: Graph, goal_id: int) -> Graph:
    while not isinstance(source_goals, Goals):
        source_goals = source_goals.goaltree
    source_data = source_goals.q(keys="name,edge,open")
    assert goal_id in source_data.keys(), f"Cannot find goal with id {goal_id}"
    target_goals: Set[int] = set()
    goals_to_add: Set[int] = {goal_id}
    goals_data: GoalsData = []
    edges_data: EdgesData = []
    options_data: OptionsData = []
    while goals_to_add:
        goal = goals_to_add.pop()
        attrs = source_data[goal]
        target_goals.add(goal)
        goals_data.append((goal, attrs["name"], attrs["open"]))
        edges_data.extend((goal, target_, type_) for target_, type_ in attrs["edge"])
        goals_to_add.update(
            set(
                edge[0]
                for edge in attrs["edge"]
                if edge[1] == EdgeType.PARENT and edge[0] not in target_goals
            )
        )
    edges_data = [edge for edge in edges_data if edge[1] in target_goals]
    remap = {
        old: idx + 2
        for idx, old in enumerate(g for g in sorted(target_goals) if g != goal_id)
    }
    remap[goal_id] = Goals.ROOT_ID
    goals_data = [
        (remap[goal_id], name, is_open) for goal_id, name, is_open in goals_data
    ]
    edges_data = [
        (remap[source], remap[target], e_type) for source, target, e_type in edges_data
    ]
    return Zoom.build(Goals.build(goals_data, edges_data, options_data), [])
