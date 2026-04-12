#!/usr/bin/env python3
"""Generate an 8x8 maze tiled with the corridor tile set, including crossings.

Crossings are modelled correctly: a crossing cell has two independent channels
(vertical N-S and horizontal E-W) that don't connect. The maze is generated as
a spanning tree on an expanded graph where crossing cells are split into two
nodes, guaranteeing no loops.
"""

import random
import subprocess
import sys
from collections import defaultdict


class Maze:
    """Maze = set of passages between grid cells."""

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.edges = set()

    def add_edge(self, u, v):
        self.edges.add((min(u, v), max(u, v)))

    def has_passage(self, u, v):
        return (min(u, v), max(u, v)) in self.edges


def cell_dirs(maze, r, c):
    """Return set of open directions for cell (r, c)."""
    dirs = set()
    if r > 0 and maze.has_passage((r, c), (r - 1, c)):
        dirs.add('N')
    if r < maze.rows - 1 and maze.has_passage((r, c), (r + 1, c)):
        dirs.add('S')
    if c < maze.cols - 1 and maze.has_passage((r, c), (r, c + 1)):
        dirs.add('E')
    if c > 0 and maze.has_passage((r, c), (r, c - 1)):
        dirs.add('W')
    return dirs


def gen_crossing_maze(rows, cols, num_crossings=4):
    """Generate a loop-free maze with crossings.

    1. Pick interior cells as crossing candidates.
    2. Build an expanded graph: crossing cells get two nodes (V-channel, H-channel),
       normal cells get one node. Vertical edges connect V-channels, horizontal
       edges connect H-channels.
    3. Run Kruskal's (crossing edges prioritised) to build a spanning tree.
    4. Cells that ended up with all 4 passages are actual crossings.
    """
    # Pick crossing cells (interior only — need all 4 neighbors)
    candidates = [(r, c) for r in range(1, rows - 1)
                   for c in range(1, cols - 1)]
    random.shuffle(candidates)
    crossing_cells = set(candidates[:num_crossings])

    # Assign node IDs for expanded graph
    node_id = {}
    nid = 0
    for r in range(rows):
        for c in range(cols):
            if (r, c) in crossing_cells:
                node_id[(r, c, 'V')] = nid; nid += 1
                node_id[(r, c, 'H')] = nid; nid += 1
            else:
                node_id[(r, c, 'X')] = nid; nid += 1

    def get_node(r, c, direction):
        if (r, c) in crossing_cells:
            return node_id[(r, c, 'V' if direction in ('N', 'S') else 'H')]
        return node_id[(r, c, 'X')]

    # Union-find
    parent = list(range(nid))
    rank = [0] * nid

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx == ry:
            return False
        if rank[rx] < rank[ry]:
            rx, ry = ry, rx
        parent[ry] = rx
        if rank[rx] == rank[ry]:
            rank[rx] += 1
        return True

    # Collect all grid edges with their expanded-graph endpoints
    crossing_edges = []
    other_edges = []
    for r in range(rows):
        for c in range(cols):
            if r + 1 < rows:
                u = get_node(r, c, 'S')
                v = get_node(r + 1, c, 'N')
                entry = (u, v, (r, c), (r + 1, c))
                if (r, c) in crossing_cells or (r + 1, c) in crossing_cells:
                    crossing_edges.append(entry)
                else:
                    other_edges.append(entry)
            if c + 1 < cols:
                u = get_node(r, c, 'E')
                v = get_node(r, c + 1, 'W')
                entry = (u, v, (r, c), (r, c + 1))
                if (r, c) in crossing_cells or (r, c + 1) in crossing_cells:
                    crossing_edges.append(entry)
                else:
                    other_edges.append(entry)

    maze = Maze(rows, cols)

    # Phase 1: prioritise crossing edges so crossings actually form
    random.shuffle(crossing_edges)
    for u, v, c1, c2 in crossing_edges:
        if union(u, v):
            maze.add_edge(c1, c2)

    # Phase 2: fill remaining with random Kruskal's
    random.shuffle(other_edges)
    for u, v, c1, c2 in other_edges:
        if union(u, v):
            maze.add_edge(c1, c2)

    # Identify actual crossings (cells that got all 4 passages)
    actual_crossings = {}
    for r, c in crossing_cells:
        dirs = cell_dirs(maze, r, c)
        if dirs >= {'N', 'S', 'E', 'W'}:
            actual_crossings[(r, c)] = random.choice(['VH', 'HV'])

    return maze, actual_crossings


def render_cell(dirs, S, R, HW, Ri, Ro, crossing=None):
    """Generate TikZ draw commands for a single cell (local coords)."""
    lines = []
    d = frozenset(dirs)

    # --- Crossings ---
    if crossing == 'VH':
        lines.append(f"    \\draw[o] (0,{R})--({S},{R}); \\draw[i] (0,{R})--({S},{R});")
        lines.append(f"    \\draw[w] ({R},0)--({R},{S});")
        lines.append(f"    \\draw[o] ({R},0)--({R},{S}); \\draw[i] ({R},0)--({R},{S});")
        return lines
    elif crossing == 'HV':
        lines.append(f"    \\draw[o] ({R},0)--({R},{S}); \\draw[i] ({R},0)--({R},{S});")
        lines.append(f"    \\draw[w] (0,{R})--({S},{R});")
        lines.append(f"    \\draw[o] (0,{R})--({S},{R}); \\draw[i] (0,{R})--({S},{R});")
        return lines

    # --- Turns: concave arcs ---
    if d == frozenset({'N', 'E'}):
        lines.append(f"    \\draw[wall] ({S-Ri},{S}) arc[start angle=180, delta angle=90, radius={Ri} cm];")
        lines.append(f"    \\draw[wall] ({S-Ro},{S}) arc[start angle=180, delta angle=90, radius={Ro} cm];")
    elif d == frozenset({'N', 'W'}):
        lines.append(f"    \\draw[wall] (0,{S-Ri}) arc[start angle=270, delta angle=90, radius={Ri} cm];")
        lines.append(f"    \\draw[wall] (0,{S-Ro}) arc[start angle=270, delta angle=90, radius={Ro} cm];")
    elif d == frozenset({'S', 'E'}):
        lines.append(f"    \\draw[wall] ({S},{Ri}) arc[start angle=90, delta angle=90, radius={Ri} cm];")
        lines.append(f"    \\draw[wall] ({S},{Ro}) arc[start angle=90, delta angle=90, radius={Ro} cm];")
    elif d == frozenset({'S', 'W'}):
        lines.append(f"    \\draw[wall] ({Ri},0) arc[start angle=0, delta angle=90, radius={Ri} cm];")
        lines.append(f"    \\draw[wall] ({Ro},0) arc[start angle=0, delta angle=90, radius={Ro} cm];")

    # --- Dead ends: U-shaped wall paths ---
    elif d == frozenset({'N'}):
        lines.append(f"    \\draw[wall] ({R-HW},{S}) -- ({R-HW},{R}) -- ({R+HW},{R}) -- ({R+HW},{S});")
    elif d == frozenset({'S'}):
        lines.append(f"    \\draw[wall] ({R-HW},0) -- ({R-HW},{R}) -- ({R+HW},{R}) -- ({R+HW},0);")
    elif d == frozenset({'E'}):
        lines.append(f"    \\draw[wall] ({S},{R+HW}) -- ({R},{R+HW}) -- ({R},{R-HW}) -- ({S},{R-HW});")
    elif d == frozenset({'W'}):
        lines.append(f"    \\draw[wall] (0,{R+HW}) -- ({R},{R+HW}) -- ({R},{R-HW}) -- (0,{R-HW});")

    # --- Straights, T-junctions, four-way: overlay approach ---
    else:
        outers = []
        inners = []

        if 'N' in dirs and 'S' in dirs:
            outers.append(f"({R},0)--({R},{S})")
            inners.append(f"({R},0)--({R},{S})")
        elif 'N' in dirs:
            outers.append(f"({R},{R})--({R},{S})")
            inners.append(f"({R},{R})--({R},{S})")
        elif 'S' in dirs:
            outers.append(f"({R},0)--({R},{R})")
            inners.append(f"({R},0)--({R},{R})")

        if 'E' in dirs and 'W' in dirs:
            outers.append(f"(0,{R})--({S},{R})")
            inners.append(f"(0,{R})--({S},{R})")
        elif 'E' in dirs:
            outers.append(f"({R},{R})--({S},{R})")
            inners.append(f"({R},{R})--({S},{R})")
        elif 'W' in dirs:
            outers.append(f"(0,{R})--({R},{R})")
            inners.append(f"(0,{R})--({R},{R})")

        for seg in outers:
            lines.append(f"    \\draw[o] {seg};")
        for seg in inners:
            lines.append(f"    \\draw[i] {seg};")

    return lines


def generate_document(rows=8, cols=8, seed=42, num_crossings=None):
    random.seed(seed)
    if num_crossings is None:
        # ~60% of interior cells are crossings for maximum density
        interior = (rows - 2) * (cols - 2)
        num_crossings = max(4, int(interior * 0.60))
    maze, crossings = gen_crossing_maze(rows, cols, num_crossings)

    # Scale tile size to fit A4 page (≈26cm usable width/height)
    max_dim = max(rows, cols)
    S = min(2.5, 26.0 / max_dim)
    R = S / 2
    HW = S * 0.14       # wall half-width scales with tile
    Ri = R - HW
    Ro = R + HW

    # Line widths scale with tile size (reference: S=2.5 → outer=7mm)
    scale = S / 2.5
    outer_w = 7 * scale    # mm
    inner_w = 4 * scale    # mm
    wipe_w = 8.5 * scale   # mm
    wall_w = 1.5 * scale   # mm

    doc = [rf"""\documentclass[border=5mm]{{standalone}}
\usepackage{{tikz}}
\usepackage[T1]{{fontenc}}
\usepackage{{lmodern}}

\begin{{document}}
\begin{{tikzpicture}}[
  o/.style={{line width={outer_w:.2f}mm, draw=black, line cap=butt}},
  i/.style={{line width={inner_w:.2f}mm, draw=white, line cap=butt}},
  w/.style={{line width={wipe_w:.2f}mm, draw=white, line cap=butt}},
  wall/.style={{line width={wall_w:.2f}mm, draw=black, line cap=butt, line join=miter}},
  bdr/.style={{draw=black!15, line width=0.3pt}},
]"""]

    doc.append(f"  % Grid lines")
    doc.append(f"  \\foreach \\i in {{0,...,{cols}}} {{")
    doc.append(f"    \\draw[bdr] (\\i*{S}, 0) -- (\\i*{S}, {rows*S});")
    doc.append(f"  }}")
    doc.append(f"  \\foreach \\i in {{0,...,{rows}}} {{")
    doc.append(f"    \\draw[bdr] (0, \\i*{S}) -- ({cols*S}, \\i*{S});")
    doc.append(f"  }}")
    doc.append("")

    if crossings:
        doc.append(f"  % {len(crossings)} crossings: {dict(crossings)}")

    for r in range(rows):
        for c in range(cols):
            dirs = cell_dirs(maze, r, c)
            x_off = c * S
            y_off = (rows - 1 - r) * S
            crossing = crossings.get((r, c))
            doc.append(f"  \\begin{{scope}}[shift={{({x_off},{y_off})}}]")
            doc.extend(render_cell(dirs, S, R, HW, Ri, Ro, crossing))
            doc.append(f"  \\end{{scope}}")

    doc.append(r"\end{tikzpicture}")
    doc.append(r"\end{document}")
    return "\n".join(doc)


if __name__ == "__main__":
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42

    latex = generate_document(rows=size, cols=size, seed=seed)
    tex_path = "grid.tex"
    with open(tex_path, "w") as f:
        f.write(latex)
    print(f"Written {tex_path}")

    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", tex_path],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("Compiled grid.pdf")
    else:
        print("pdflatex failed:")
        print(result.stdout[-2000:])
        sys.exit(1)
