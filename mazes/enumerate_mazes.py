"""
Enumerate perfect mazes on n×m grids, classified by spanning tree isomorphism.

A perfect maze on an n×m grid ↔ a spanning tree of the grid graph P_n × P_m.
Two mazes are "structurally the same" iff their spanning trees are isomorphic
as abstract graphs (ignoring grid coordinates).

Question: for each tree isomorphism class, how many grid embeddings exist?
"""

import numpy as np
from collections import defaultdict, Counter
from itertools import combinations
import time
import sys


# ── Grid graph construction ──────────────────────────────────────────────

def grid_graph(rows, cols):
    """Build grid graph P_rows × P_cols. Returns (vertices, edges) with
    vertices as (row, col) tuples and edges as pairs of vertices."""
    vertices = [(r, c) for r in range(rows) for c in range(cols)]
    edges = []
    for r in range(rows):
        for c in range(cols):
            if c + 1 < cols:
                edges.append(((r, c), (r, c + 1)))  # horizontal
            if r + 1 < rows:
                edges.append(((r, c), (r + 1, c)))  # vertical
    return vertices, edges


# ── Kirchhoff's matrix-tree theorem ─────────────────────────────────────

def count_spanning_trees(rows, cols):
    """Count spanning trees of P_rows × P_cols using Kirchhoff's theorem.

    The number = det of any cofactor of the Laplacian. We use the eigenvalue
    product formula: τ(G) = (1/n) ∏ λ_i for nonzero eigenvalues λ_i.

    For the grid graph, eigenvalues of the Laplacian are:
        μ_{i,j} = (2 - 2cos(πi/rows)) + (2 - 2cos(πj/cols))
    for i=0..rows-1, j=0..cols-1.
    """
    n = rows * cols
    product = 1.0
    for i in range(rows):
        for j in range(cols):
            if i == 0 and j == 0:
                continue  # skip the zero eigenvalue
            lam = (2 - 2 * np.cos(np.pi * i / rows)) + \
                  (2 - 2 * np.cos(np.pi * j / cols))
            product *= lam
    return round(product / n)


# ── Union-Find with undo (no path compression) ──────────────────────────

class UndoableUF:
    """Union-Find supporting O(1) undo of union operations.

    Path compression is disabled so that each union touches exactly
    two entries, making rollback trivial. find() is O(log n) instead
    of O(α(n)), but n ≤ 64 for an 8×8 grid, so this is negligible.
    """
    __slots__ = ('parent', 'rank', 'components')

    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.components = n

    def find(self, x):
        while self.parent[x] != x:
            x = self.parent[x]
        return x

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return None
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        # Attach py under px
        save = (py, self.parent[py], px, self.rank[px])
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        self.components -= 1
        return save

    def undo(self, save):
        py, old_parent, px, old_rank = save
        self.parent[py] = old_parent
        self.rank[px] = old_rank
        self.components += 1


# ── Spanning tree enumeration (backtracking with UF) ────────────────────

def enumerate_spanning_trees(rows, cols):
    """Yield all spanning trees of P_rows × P_cols as lists of edge indices.

    Uses backtracking: for each edge, decide include/exclude.
    Prune when: (a) including would create a cycle, (b) not enough
    edges remain to complete the tree.
    """
    vertices, edges = grid_graph(rows, cols)
    n = len(vertices)
    m = len(edges)
    v_to_i = {v: i for i, v in enumerate(vertices)}
    # Convert edges to integer pairs for UF
    int_edges = [(v_to_i[u], v_to_i[v]) for u, v in edges]

    uf = UndoableUF(n)
    needed = n - 1  # edges still needed

    def backtrack(idx, needed):
        if needed == 0:
            yield []
            return
        remaining = m - idx
        if remaining < needed:
            return
        for i in range(idx, m - needed + 1):
            u, v = int_edges[i]
            save = uf.union(u, v)
            if save is not None:  # not a cycle
                for rest in backtrack(i + 1, needed - 1):
                    yield [i] + rest
                uf.undo(save)

    yield from backtrack(0, n - 1)


# ── Tree canonical form (AHU-style) ─────────────────────────────────────

def tree_canonical_form(n_vertices, edge_list):
    """Compute a canonical hash for an unrooted tree.

    Algorithm:
    1. Find the center (1 or 2 nodes with minimum eccentricity)
       by iteratively peeling leaves.
    2. Root at the center.
    3. Recursively encode subtrees as sorted tuples.

    Two trees get the same canonical form iff they are isomorphic.
    """
    adj = [[] for _ in range(n_vertices)]
    for u, v in edge_list:
        adj[u].append(v)
        adj[v].append(u)

    # Find center by iterative leaf removal
    degree = [len(adj[i]) for i in range(n_vertices)]
    remaining = set(range(n_vertices))
    leaves = [i for i in range(n_vertices) if degree[i] <= 1]

    while len(remaining) > 2:
        new_leaves = []
        for leaf in leaves:
            remaining.discard(leaf)
            for v in adj[leaf]:
                if v in remaining:
                    degree[v] -= 1
                    if degree[v] == 1:
                        new_leaves.append(v)
        leaves = new_leaves

    centers = sorted(remaining)

    def rooted_form(root, parent):
        children = []
        for v in adj[root]:
            if v != parent:
                children.append(rooted_form(v, root))
        children.sort()
        return tuple(children)

    if len(centers) == 1:
        return ('C', rooted_form(centers[0], -1))
    else:
        # Edge-centered: root at each center, combine canonically
        f0 = rooted_form(centers[0], centers[1])
        f1 = rooted_form(centers[1], centers[0])
        return ('E', min(f0, f1), max(f0, f1))


# ── Tree invariants ─────────────────────────────────────────────────────

def tree_invariants(n_vertices, edge_list):
    """Compute descriptive invariants of a tree."""
    adj = [[] for _ in range(n_vertices)]
    for u, v in edge_list:
        adj[u].append(v)
        adj[v].append(u)

    degrees = sorted([len(adj[i]) for i in range(n_vertices)], reverse=True)
    n_leaves = sum(1 for d in degrees if d == 1)
    max_degree = degrees[0]

    # Diameter via double BFS
    def bfs_farthest(start):
        dist = [-1] * n_vertices
        dist[start] = 0
        queue = [start]
        farthest = start
        for node in queue:
            for v in adj[node]:
                if dist[v] == -1:
                    dist[v] = dist[node] + 1
                    queue.append(v)
                    if dist[v] > dist[farthest]:
                        farthest = v
        return farthest, dist[farthest]

    far1, _ = bfs_farthest(0)
    _, diameter = bfs_farthest(far1)

    # Wiener index (sum of all pairwise distances)
    wiener = 0
    for start in range(n_vertices):
        dist = [-1] * n_vertices
        dist[start] = 0
        queue = [start]
        for node in queue:
            for v in adj[node]:
                if dist[v] == -1:
                    dist[v] = dist[node] + 1
                    queue.append(v)
                    wiener += dist[v]
    wiener //= 2  # each pair counted twice

    return {
        'degree_seq': tuple(degrees),
        'leaves': n_leaves,
        'max_degree': max_degree,
        'diameter': diameter,
        'wiener': wiener,
    }


# ── Main analysis ───────────────────────────────────────────────────────

def analyze_grid(rows, cols, max_trees=500000):
    """Full analysis of spanning trees of P_rows × P_cols."""
    n = rows * cols
    vertices, edges = grid_graph(rows, cols)
    v_to_i = {v: i for i, v in enumerate(vertices)}
    int_edges = [(v_to_i[u], v_to_i[v]) for u, v in edges]

    # Kirchhoff count
    kirchhoff_count = count_spanning_trees(rows, cols)
    print(f"\n{'='*60}")
    print(f"  {rows}×{cols} Grid  ({n} vertices, {len(edges)} edges)")
    print(f"  Spanning trees (Kirchhoff): {kirchhoff_count:,}")
    print(f"{'='*60}")

    if kirchhoff_count > max_trees:
        print(f"  ⚠ Too many to enumerate (limit {max_trees:,}). Showing count only.")
        return kirchhoff_count, None

    # Enumerate and classify
    class_counts = Counter()  # canonical_form → count
    class_invariants = {}     # canonical_form → invariants dict

    t0 = time.time()
    count = 0
    for tree_edges_idx in enumerate_spanning_trees(rows, cols):
        tree_edges = [int_edges[i] for i in tree_edges_idx]
        cf = tree_canonical_form(n, tree_edges)
        class_counts[cf] += 1
        if cf not in class_invariants:
            class_invariants[cf] = tree_invariants(n, tree_edges)
        count += 1
        if count % 10000 == 0:
            elapsed = time.time() - t0
            print(f"    ... {count:,} trees enumerated ({elapsed:.1f}s)", file=sys.stderr)

    elapsed = time.time() - t0

    # Verify count
    assert count == kirchhoff_count, \
        f"Enumerated {count} but Kirchhoff says {kirchhoff_count}"

    # Sort classes by embedding count (descending)
    sorted_classes = sorted(class_counts.items(), key=lambda x: -x[1])

    print(f"  Enumerated: {count:,} trees in {elapsed:.2f}s")
    print(f"  Isomorphism classes: {len(sorted_classes)}")
    print()

    # Table header
    print(f"  {'#':>4}  {'Embeddings':>10}  {'%':>6}  {'Leaves':>6}  "
          f"{'Diam':>4}  {'MaxDeg':>6}  {'Wiener':>6}  Degree sequence")
    print(f"  {'─'*4}  {'─'*10}  {'─'*6}  {'─'*6}  {'─'*4}  {'─'*6}  {'─'*6}  {'─'*30}")

    for rank, (cf, emb_count) in enumerate(sorted_classes, 1):
        inv = class_invariants[cf]
        pct = 100 * emb_count / count
        deg_str = str(list(inv['degree_seq']))
        if len(deg_str) > 40:
            deg_str = deg_str[:37] + "..."
        print(f"  {rank:>4}  {emb_count:>10,}  {pct:>5.1f}%  {inv['leaves']:>6}  "
              f"{inv['diameter']:>4}  {inv['max_degree']:>6}  {inv['wiener']:>6}  {deg_str}")
        if rank >= 50 and len(sorted_classes) > 55:
            print(f"  ... ({len(sorted_classes) - 50} more classes)")
            break

    # Summary statistics
    print()
    emb_counts = list(class_counts.values())
    print(f"  Embedding count stats:")
    print(f"    min = {min(emb_counts):,},  max = {max(emb_counts):,},  "
          f"mean = {sum(emb_counts)/len(emb_counts):.1f},  "
          f"median = {sorted(emb_counts)[len(emb_counts)//2]:,}")

    # Distribution of leaves
    leaf_dist = Counter()
    for cf, emb_count in class_counts.items():
        leaf_dist[class_invariants[cf]['leaves']] += emb_count
    print(f"\n  Trees by leaf count (summed over embeddings):")
    for leaves in sorted(leaf_dist):
        pct = 100 * leaf_dist[leaves] / count
        print(f"    {leaves} leaves: {leaf_dist[leaves]:>8,} trees ({pct:>5.1f}%)")

    # Distribution of diameter
    diam_dist = Counter()
    for cf, emb_count in class_counts.items():
        diam_dist[class_invariants[cf]['diameter']] += emb_count
    print(f"\n  Trees by diameter (summed over embeddings):")
    for diam in sorted(diam_dist):
        pct = 100 * diam_dist[diam] / count
        print(f"    diameter {diam}: {diam_dist[diam]:>8,} trees ({pct:>5.1f}%)")

    return kirchhoff_count, sorted_classes


# ── Run ─────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    grids = [(2, 2), (2, 3), (2, 4), (2, 5), (3, 3), (3, 4), (4, 4)]

    # First, show Kirchhoff counts for larger grids too
    print("Kirchhoff spanning tree counts:")
    for r in range(1, 9):
        for c in range(r, 9):
            if r * c <= 64:
                cnt = count_spanning_trees(r, c)
                print(f"  {r}×{c}: {cnt:>20,}")
    print()

    # Full analysis for tractable sizes
    for rows, cols in grids:
        analyze_grid(rows, cols)
