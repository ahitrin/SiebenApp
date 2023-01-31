import sqlite3
from os import path
from typing import Callable, Optional

from siebenapp.autolink import AutoLink, AutoLinkData
from siebenapp.domain import Graph
from siebenapp.enumeration import Enumeration
from siebenapp.goaltree import Goals
from siebenapp.layers import all_layers, get_root
from siebenapp.zoom import Zoom, ZoomData

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
    # 8
    [
        """create table autolink (
            goal integer primary key,
            keyword text not null,
            foreign key (goal) references goals(goal_id)
        )""",
    ],
]


def save(goals: Graph, filename: str) -> None:
    if path.isfile(filename):
        connection = sqlite3.connect(filename)
        run_migrations(connection)
        save_updates(goals, connection)
    else:
        connection = sqlite3.connect(filename)
        save_connection(goals, connection)

    connection.close()


def save_connection(goals: Graph, connection) -> None:
    run_migrations(connection)
    root_goals: Goals = get_root(goals)
    goals_export, edges_export, select_export = Goals.export(root_goals)
    zoom_goals = goals
    while not isinstance(zoom_goals, Zoom):
        zoom_goals = zoom_goals.goaltree
    zoom_export = Zoom.export(zoom_goals)
    autolink_goals = goals
    while not isinstance(autolink_goals, AutoLink):
        autolink_goals = autolink_goals.goaltree
    autolink_export = AutoLink.export(autolink_goals)
    cur = connection.cursor()
    cur.executemany("insert into goals values (?,?,?)", goals_export)
    cur.executemany("insert into edges values (?,?,?)", edges_export)
    cur.executemany("insert into settings values (?,?)", select_export)
    cur.executemany("insert into zoom values (?, ?)", zoom_export)
    cur.executemany("insert into autolink values(?, ?)", autolink_export)
    root_goals._events.clear()
    connection.commit()


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
        "add_autolink": ["insert into autolink values (?, ?)"],
        "remove_autolink": ["delete from autolink where goal=?"],
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


def load(
    filename: str, message_fn: Optional[Callable[[str], None]] = None
) -> Enumeration:
    zoom_data: ZoomData = []
    autolink_data: AutoLinkData = []
    if path.isfile(filename):
        connection = sqlite3.connect(filename)
        run_migrations(connection)
        cur = connection.cursor()
        names = list(cur.execute("select * from goals"))
        edges = list(cur.execute("select parent, child, reltype from edges"))
        settings = list(cur.execute("select * from settings"))
        zoom_data = list(cur.execute("select * from zoom"))
        autolink_data = list(cur.execute("select * from autolink"))
        cur.close()
        goals = Goals.build(names, edges, settings, message_fn)
    else:
        goals = Goals("Rename me", message_fn)
    result = Enumeration(all_layers(goals, zoom_data, autolink_data))
    result.verify()
    return result


def run_migrations(
    conn: sqlite3.Connection, migrations_to_run: Optional[list[list[str]]] = None
) -> None:
    migrations: list[list[str]] = (
        MIGRATIONS if migrations_to_run is None else migrations_to_run
    )
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
