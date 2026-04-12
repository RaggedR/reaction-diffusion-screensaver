#!/usr/bin/env python3
"""Kruskal's algorithm for knotted mazes.

A knotted maze is a maze on an expanded graph where designated "crossing"
cells are split into two independent channel-nodes:
  - V-channel: connects N and S neighbors
  - H-channel: connects E and W neighbors

The two channels share the same grid cell but are topologically disjoint —
a walker on the V-channel cannot switch to the H-channel at a crossing.

Kruskal's algorithm is ideal here because it operates on abstract nodes
and edges via union-find, completely agnostic to the graph's geometry.
"""

import random
import subprocess
import sys


# ---------------------------------------------------------------------------
# Union-Find
# ---------------------------------------------------------------------------

class UnionFind:
    """Union-find with path compression and union by rank."""

    def __init__(self):
        self.parent = {}
        self.rank = {}

    def make_set(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        return True


# ---------------------------------------------------------------------------
# Knotted graph construction
# ---------------------------------------------------------------------------

def build_knotted_graph(rows, cols, crossing_cells):
    """Build the expanded graph for a knotted maze.

    Returns:
        nodes: set of node identifiers
        edges: list of (node_a, node_b, cell_a, cell_b) tuples

    Node identifiers:
        (r, c, 'X')  — normal cell (single node)
        (r, c, 'V')  — V-channel of a crossing cell
        (r, c, 'H')  — H-channel of a crossing cell
    """
    def node(r, c, direction):
        if (r, c) in crossing_cells:
            return (r, c, 'V') if direction in ('N', 'S') else (r, c, 'H')
        return (r, c, 'X')

    nodes = set()
    for r in range(rows):
        for c in range(cols):
            if (r, c) in crossing_cells:
                nodes.add((r, c, 'V'))
                nodes.add((r, c, 'H'))
            else:
                nodes.add((r, c, 'X'))

    edges = []
    for r in range(rows):
        for c in range(cols):
            # Vertical edge: this cell's S-channel ↔ southern neighbor's N-channel
            if r + 1 < rows:
                u = node(r, c, 'S')
                v = node(r + 1, c, 'N')
                edges.append((u, v, (r, c), (r + 1, c)))
            # Horizontal edge: this cell's E-channel ↔ eastern neighbor's W-channel
            if c + 1 < cols:
                u = node(r, c, 'E')
                v = node(r, c + 1, 'W')
                edges.append((u, v, (r, c), (r, c + 1)))

    return nodes, edges


# ---------------------------------------------------------------------------
# Kruskal's algorithm
# ---------------------------------------------------------------------------

def _get_dirs(maze_edges, rows, cols, r, c):
    """Return set of open directions for cell (r, c) from edge set."""
    dirs = set()
    if r > 0 and (min((r, c), (r-1, c)), max((r, c), (r-1, c))) in maze_edges:
        dirs.add('N')
    if r < rows-1 and (min((r, c), (r+1, c)), max((r, c), (r+1, c))) in maze_edges:
        dirs.add('S')
    if c < cols-1 and (min((r, c), (r, c+1)), max((r, c), (r, c+1))) in maze_edges:
        dirs.add('E')
    if c > 0 and (min((r, c), (r, c-1)), max((r, c), (r, c-1))) in maze_edges:
        dirs.add('W')
    return dirs


def kruskal_knotted(rows, cols, crossing_cells, density=0.0, dead_end_fill=0.0):
    """Generate a knotted maze using Kruskal's algorithm.

    Args:
        rows, cols: grid dimensions
        crossing_cells: set of (r,c) to designate as crossings
        density: 0.0–1.0, fraction of rejected (cycle-creating) edges to add
                 back after spanning tree. 0 = pure tree, 1 = all possible edges.
                 Higher values create loops (multiple solutions) and fill space.
        dead_end_fill: 0.0–1.0, fraction of dead ends to eliminate by adding
                       a second passage. Reduces branchiness.

    Returns:
        maze_edges: set of ((r1,c1), (r2,c2)) passages
        actual_crossings: dict (r,c) -> 'VH' or 'HV'
    """
    nodes, edges = build_knotted_graph(rows, cols, crossing_cells)

    uf = UnionFind()
    for n in nodes:
        uf.make_set(n)

    # Shuffle edges — this is the "random weight" step in randomized Kruskal's
    random.shuffle(edges)

    # Prioritise edges touching crossings so crossings actually form
    edges.sort(key=lambda e: 0 if (e[2] in crossing_cells or e[3] in crossing_cells) else 1)

    maze_edges = set()
    rejected = []  # edges that would create cycles

    for u, v, c1, c2 in edges:
        if uf.union(u, v):
            maze_edges.add((min(c1, c2), max(c1, c2)))
        else:
            rejected.append((c1, c2))

    # --- Density: add back rejected edges to create loops ---
    if density > 0 and rejected:
        random.shuffle(rejected)
        num_extra = int(len(rejected) * density)
        for c1, c2 in rejected[:num_extra]:
            maze_edges.add((min(c1, c2), max(c1, c2)))

    # --- Dead-end fill: eliminate dead ends by adding a second passage ---
    if dead_end_fill > 0:
        dead_ends = []
        for r in range(rows):
            for c in range(cols):
                if (r, c) in crossing_cells:
                    continue
                dirs = _get_dirs(maze_edges, rows, cols, r, c)
                if len(dirs) == 1:
                    dead_ends.append((r, c))
        random.shuffle(dead_ends)
        num_fill = int(len(dead_ends) * dead_end_fill)
        for r, c in dead_ends[:num_fill]:
            dirs = _get_dirs(maze_edges, rows, cols, r, c)
            if len(dirs) >= 2:
                continue  # already fixed by a prior fill
            # Try adding a passage in a direction we don't have
            candidates = []
            if 'N' not in dirs and r > 0:
                candidates.append((r - 1, c))
            if 'S' not in dirs and r < rows - 1:
                candidates.append((r + 1, c))
            if 'E' not in dirs and c < cols - 1:
                candidates.append((r, c + 1))
            if 'W' not in dirs and c > 0:
                candidates.append((r, c - 1))
            if candidates:
                nb = random.choice(candidates)
                maze_edges.add((min((r, c), nb), max((r, c), nb)))

    # Identify which crossing cells actually got all 4 passages
    actual_crossings = {}
    for r, c in crossing_cells:
        dirs = _get_dirs(maze_edges, rows, cols, r, c)
        if dirs >= {'N', 'S', 'E', 'W'}:
            actual_crossings[(r, c)] = random.choice(['VH', 'HV'])

    return maze_edges, actual_crossings


# ---------------------------------------------------------------------------
# TikZ rendering
# ---------------------------------------------------------------------------

def cell_dirs(maze_edges, rows, cols, r, c):
    """Return set of open directions for cell (r, c)."""
    dirs = set()
    if r > 0 and (min((r, c), (r-1, c)), max((r, c), (r-1, c))) in maze_edges:
        dirs.add('N')
    if r < rows - 1 and (min((r, c), (r+1, c)), max((r, c), (r+1, c))) in maze_edges:
        dirs.add('S')
    if c < cols - 1 and (min((r, c), (r, c+1)), max((r, c), (r, c+1))) in maze_edges:
        dirs.add('E')
    if c > 0 and (min((r, c), (r, c-1)), max((r, c), (r, c-1))) in maze_edges:
        dirs.add('W')
    return dirs


def render_cell(dirs, S, R, HW, Ri, Ro, crossing=None):
    """Generate TikZ draw commands for one cell in local coords."""
    lines = []
    d = frozenset(dirs)

    # Crossings
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

    # Turns — concave arcs centered at tile corner
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

    # Dead ends — U-shaped wall paths
    elif d == frozenset({'N'}):
        lines.append(f"    \\draw[wall] ({R-HW},{S}) -- ({R-HW},{R}) -- ({R+HW},{R}) -- ({R+HW},{S});")
    elif d == frozenset({'S'}):
        lines.append(f"    \\draw[wall] ({R-HW},0) -- ({R-HW},{R}) -- ({R+HW},{R}) -- ({R+HW},0);")
    elif d == frozenset({'E'}):
        lines.append(f"    \\draw[wall] ({S},{R+HW}) -- ({R},{R+HW}) -- ({R},{R-HW}) -- ({S},{R-HW});")
    elif d == frozenset({'W'}):
        lines.append(f"    \\draw[wall] (0,{R+HW}) -- ({R},{R+HW}) -- ({R},{R-HW}) -- (0,{R-HW});")

    # Straights, T-junctions, four-way — overlay approach
    else:
        outers, inners = [], []
        if 'N' in dirs and 'S' in dirs:
            outers.append(f"({R},0)--({R},{S})"); inners.append(f"({R},0)--({R},{S})")
        elif 'N' in dirs:
            outers.append(f"({R},{R})--({R},{S})"); inners.append(f"({R},{R})--({R},{S})")
        elif 'S' in dirs:
            outers.append(f"({R},0)--({R},{R})"); inners.append(f"({R},0)--({R},{R})")
        if 'E' in dirs and 'W' in dirs:
            outers.append(f"(0,{R})--({S},{R})"); inners.append(f"(0,{R})--({S},{R})")
        elif 'E' in dirs:
            outers.append(f"({R},{R})--({S},{R})"); inners.append(f"({R},{R})--({S},{R})")
        elif 'W' in dirs:
            outers.append(f"(0,{R})--({R},{R})"); inners.append(f"(0,{R})--({R},{R})")
        for seg in outers:
            lines.append(f"    \\draw[o] {seg};")
        for seg in inners:
            lines.append(f"    \\draw[i] {seg};")

    return lines


def generate_document(rows, cols, seed=42, crossing_fraction=0.60,
                      density=0.0, dead_end_fill=0.0):
    """Generate a complete TikZ document for a knotted Kruskal maze.

    Args:
        rows, cols: grid dimensions
        seed: random seed for reproducibility
        crossing_fraction: 0.0–1.0, fraction of interior cells that are crossings
        density: 0.0–1.0, extra edges beyond spanning tree (creates loops)
        dead_end_fill: 0.0–1.0, fraction of dead ends to eliminate
    """
    random.seed(seed)

    # Pick crossing cells (interior only)
    interior = [(r, c) for r in range(1, rows - 1) for c in range(1, cols - 1)]
    random.shuffle(interior)
    num_crossings = max(0, int(len(interior) * crossing_fraction))
    crossing_cells = set(interior[:num_crossings])

    maze_edges, crossings = kruskal_knotted(
        rows, cols, crossing_cells,
        density=density, dead_end_fill=dead_end_fill,
    )

    # Scale tile size to fit ~26cm
    max_dim = max(rows, cols)
    S = min(2.5, 26.0 / max_dim)
    R = S / 2
    HW = S * 0.14
    Ri = R - HW
    Ro = R + HW

    scale = S / 2.5
    outer_w = 7 * scale
    inner_w = 4 * scale
    wipe_w = 8.5 * scale
    wall_w = 1.5 * scale

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

    # Grid lines
    doc.append(f"  \\foreach \\i in {{0,...,{cols}}} {{")
    doc.append(f"    \\draw[bdr] (\\i*{S}, 0) -- (\\i*{S}, {rows * S});")
    doc.append(f"  }}")
    doc.append(f"  \\foreach \\i in {{0,...,{rows}}} {{")
    doc.append(f"    \\draw[bdr] (0, \\i*{S}) -- ({cols * S}, \\i*{S});")
    doc.append(f"  }}")

    doc.append(f"  % {len(crossings)} actual crossings")

    for r in range(rows):
        for c in range(cols):
            dirs = cell_dirs(maze_edges, rows, cols, r, c)
            x_off = c * S
            y_off = (rows - 1 - r) * S
            crossing = crossings.get((r, c))
            doc.append(f"  \\begin{{scope}}[shift={{({x_off:.4f},{y_off:.4f})}}]")
            doc.extend(render_cell(dirs, S, R, HW, Ri, Ro, crossing))
            doc.append(f"  \\end{{scope}}")

    doc.append(r"\end{tikzpicture}")
    doc.append(r"\end{document}")
    return "\n".join(doc)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Knotted Kruskal maze generator")
    parser.add_argument("size", nargs="?", type=int, default=20, help="Grid size (default: 20)")
    parser.add_argument("seed", nargs="?", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("-c", "--crossings", type=float, default=0.40,
                        help="Crossing fraction 0.0-1.0 (default: 0.40)")
    parser.add_argument("-d", "--density", type=float, default=0.0,
                        help="Extra edge density 0.0-1.0 (default: 0.0)")
    parser.add_argument("-f", "--fill", type=float, default=0.0,
                        help="Dead-end fill fraction 0.0-1.0 (default: 0.0)")
    args = parser.parse_args()

    size = args.size
    seed = args.seed
    latex = generate_document(
        rows=size, cols=size, seed=seed,
        crossing_fraction=args.crossings,
        density=args.density,
        dead_end_fill=args.fill,
    )
    tex_path = "kruskal.tex"
    with open(tex_path, "w") as f:
        f.write(latex)
    print(f"Written {tex_path}  ({size}x{size})")

    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", tex_path],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("Compiled kruskal.pdf")
    else:
        print("pdflatex failed:")
        print(result.stdout[-2000:])
        sys.exit(1)
