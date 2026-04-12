"""
Knotted mazes: Celtic knot patterns on a grid.

Model: n×m grid of crossing points on a torus (periodic boundaries).
At each crossing, choose one of three connection types:
  CROSS:    N↔S  and  E↔W   (two strands crossing)
  SMOOTH_A: N↔E  and  S↔W   (northeast smoothing)
  SMOOTH_B: N↔W  and  S↔E   (northwest smoothing)

Strands form closed loops. We compute:
  - Number of components
  - Writhe (sum of crossing signs)
  - Kauffman bracket polynomial → Jones polynomial
"""

import numpy as np
from collections import Counter
from itertools import product as iproduct
from fractions import Fraction

# ── Crossing types ───────��───────────────────────────────

CROSS = 0       # N↔S, E↔W (strands cross)
SMOOTH_A = 1    # N↔E, S↔W
SMOOTH_B = 2    # N↔W, S↔E

# Internal port connections for each type
# Given entry direction, what's the exit direction?
CONNECTIONS = {
    CROSS:    {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'},
    SMOOTH_A: {'N': 'E', 'E': 'N', 'S': 'W', 'W': 'S'},
    SMOOTH_B: {'N': 'W', 'W': 'N', 'S': 'E', 'E': 'S'},
}

# When leaving in direction d, which cell do we enter, from which direction?
OPPOSITE = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
MOVE = {
    'N': (-1, 0),
    'S': (1, 0),
    'E': (0, 1),
    'W': (0, -1),
}


# ── Strand tracing ──────────────────────────────────────

def trace_strands(grid, rows, cols, periodic=True):
    """Trace all strand components through the grid.

    Returns list of strands, each a list of (row, col, entry_dir) tuples.
    """
    visited = set()  # (row, col, entry_dir)
    strands = []

    for start_r in range(rows):
        for start_c in range(cols):
            for start_d in ['N', 'S', 'E', 'W']:
                if (start_r, start_c, start_d) in visited:
                    continue

                strand = []
                r, c, d = start_r, start_c, start_d

                while True:
                    if (r, c, d) in visited:
                        break
                    visited.add((r, c, d))
                    strand.append((r, c, d))

                    # Exit direction
                    cell_type = grid[r][c]
                    d_out = CONNECTIONS[cell_type][d]
                    visited.add((r, c, d_out))  # mark exit too

                    # Move to next cell
                    dr, dc = MOVE[d_out]
                    if periodic:
                        r = (r + dr) % rows
                        c = (c + dc) % cols
                    else:
                        r, c = r + dr, c + dc
                        if r < 0 or r >= rows or c < 0 or c >= cols:
                            break  # hit boundary
                    d = OPPOSITE[d_out]

                if strand:
                    strands.append(strand)

    return strands


def count_components(grid, rows, cols, periodic=True):
    """Count strand components."""
    return len(trace_strands(grid, rows, cols, periodic))


# ── Writhe (sum of crossing signs) ──────────────────────

def crossing_sign(r, c, grid, rows, cols):
    """Sign of crossing at (r,c): +1 or -1 based on checkerboard convention.

    Standard convention: crossings at (r,c) with (r+c) even get +1,
    odd get -1. This ensures alternating over/under.
    """
    if grid[r][c] != CROSS:
        return 0
    return 1 if (r + c) % 2 == 0 else -1


def writhe(grid, rows, cols):
    """Writhe = sum of crossing signs."""
    w = 0
    for r in range(rows):
        for c in range(cols):
            w += crossing_sign(r, c, grid, rows, cols)
    return w


# ── Kauffman bracket (Laurent polynomial in A) ─────────

def kauffman_bracket(grid, rows, cols, periodic=True):
    """Compute the Kauffman bracket <D> as a Laurent polynomial in A.

    <D> = sum over all smoothings S:
          A^{a(S) - b(S)} * (-A^2 - A^{-2})^{|S|-1}

    where a(S) = number of A-smoothings, b(S) = number of B-smoothings,
    |S| = number of loops after smoothing.

    Returns dict: {power_of_A: coefficient}
    """
    # Find all crossing positions
    crossings = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == CROSS:
                crossings.append((r, c))

    n_cross = len(crossings)
    if n_cross == 0:
        # No crossings: bracket = (-A^2 - A^{-2})^{loops - 1}
        loops = count_components(grid, rows, cols, periodic)
        return _d_power(loops - 1)

    # Sum over all 2^n smoothings
    bracket = {}

    for smoothing in iproduct([SMOOTH_A, SMOOTH_B], repeat=n_cross):
        # Create smoothed diagram
        smoothed = [row[:] for row in grid]
        a_count = 0
        b_count = 0
        for idx, (r, c) in enumerate(crossings):
            smoothed[r][c] = smoothing[idx]
            if smoothing[idx] == SMOOTH_A:
                a_count += 1
            else:
                b_count += 1

        loops = count_components(smoothed, rows, cols, periodic)

        # Weight: A^{a-b} * d^{loops-1} where d = -A^2 - A^{-2}
        base_power = a_count - b_count
        d_poly = _d_power(loops - 1)

        for power, coeff in d_poly.items():
            p = power + base_power
            bracket[p] = bracket.get(p, 0) + coeff

    return bracket


def _d_power(n):
    """Compute d^n as a Laurent polynomial in A, where d = -A^2 - A^{-2}."""
    if n == 0:
        return {0: 1}
    if n < 0:
        raise ValueError("Negative power of d")

    # d = -A^2 - A^{-2}
    d = {2: -1, -2: -1}
    result = {0: 1}
    for _ in range(n):
        result = _poly_mul(result, d)
    return result


def _poly_mul(p1, p2):
    """Multiply two Laurent polynomials."""
    result = {}
    for k1, c1 in p1.items():
        for k2, c2 in p2.items():
            k = k1 + k2
            result[k] = result.get(k, 0) + c1 * c2
    return {k: v for k, v in result.items() if v != 0}


def format_poly(poly):
    """Format Laurent polynomial as string."""
    if not poly:
        return "0"
    terms = []
    for power in sorted(poly.keys()):
        coeff = poly[power]
        if coeff == 0:
            continue
        if power == 0:
            terms.append(f"{coeff}")
        elif power == 1:
            terms.append(f"{coeff}A" if coeff != 1 else "A")
        elif power == -1:
            terms.append(f"{coeff}A⁻¹" if coeff != 1 else "A���¹")
        else:
            exp = str(abs(power))
            sign = "⁻" if power < 0 else ""
            sup = ''.join('⁰¹²³⁴⁵⁶⁷⁸⁹'[int(d)] for d in exp)
            if coeff == 1:
                terms.append(f"A{sign}{sup}")
            elif coeff == -1:
                terms.append(f"-A{sign}{sup}")
            else:
                terms.append(f"{coeff}A{sign}{sup}")
    return " + ".join(terms).replace("+ -", "- ")


# ── Grid generation ──��──────────────────────────────────

def all_cross_grid(rows, cols):
    """Grid where every cell is a crossing."""
    return [[CROSS] * cols for _ in range(rows)]


def all_smooth_a_grid(rows, cols):
    return [[SMOOTH_A] * cols for _ in range(rows)]


def random_grid(rows, cols, cross_prob=0.5, rng=None):
    """Random grid with given crossing probability."""
    if rng is None:
        rng = np.random.default_rng()
    grid = []
    for r in range(rows):
        row = []
        for c in range(cols):
            if rng.random() < cross_prob:
                row.append(CROSS)
            else:
                row.append(rng.choice([SMOOTH_A, SMOOTH_B]))
        grid.append(row)
    return grid


def draw_knot_ascii(grid, rows, cols):
    """Draw a small knot pattern in ASCII."""
    TYPE_CHAR = {CROSS: '╳', SMOOTH_A: '╮╰', SMOOTH_B: '╭╯'}
    # Simple representation: just show the cell types
    lines = []
    for r in range(rows):
        line = ''
        for c in range(cols):
            t = grid[r][c]
            if t == CROSS:
                line += ' ╳ '
            elif t == SMOOTH_A:
                line += ' ⌐ '
            else:
                line += ' ¬ '
        lines.append(line)
    return '\n'.join(lines)


# ── Main analysis ───────────────────────────────────────

if __name__ == '__main__':

    print("═══════════════════════════════════════════════════════")
    print("  Knotted Mazes: Celtic knot patterns on a grid")
    print("��════════════════════��══════════════════════════════���══")
    print()

    # ── Small cases: enumerate all patterns ──

    for rows, cols in [(2, 2), (2, 3), (3, 3)]:
        n = rows * cols
        print(f"  {rows}×{cols} torus: {n} crossings, {3**n} patterns, {2**n} smoothing states")

        # Enumerate all 3^n patterns (cross/smooth_a/smooth_b at each cell)
        component_dist = Counter()
        all_cross_components = None

        for pattern in iproduct([CROSS, SMOOTH_A, SMOOTH_B], repeat=n):
            grid = [list(pattern[r*cols:(r+1)*cols]) for r in range(rows)]
            nc = count_components(grid, rows, cols, periodic=True)
            component_dist[nc] += 1

            if all(t == CROSS for t in pattern):
                all_cross_components = nc

        total = sum(component_dist.values())
        print(f"    All-crossing pattern: {all_cross_components} components")
        print(f"    Component distribution:")
        for nc in sorted(component_dist):
            print(f"      {nc} components: {component_dist[nc]:>6} patterns "
                  f"({100*component_dist[nc]/total:.1f}%)")
        print()

    # ── Kauffman bracket for small examples ──

    print("═══���═══════════════════════════════════════════════════")
    print("  Kauffman bracket / Jones polynomial")
    print("══════════════════════════════════════════════════���════")
    print()

    for rows, cols in [(2, 2), (2, 3)]:
        grid = all_cross_grid(rows, cols)
        n_cross = rows * cols
        nc = count_components(grid, rows, cols, periodic=True)
        w = writhe(grid, rows, cols)

        print(f"  {rows}×{cols} torus, all crossings:")
        print(f"    Crossings: {n_cross}")
        print(f"    Components: {nc}")
        print(f"    Writhe: {w}")

        bracket = kauffman_bracket(grid, rows, cols, periodic=True)
        print(f"    ⟨D⟩ = {format_poly(bracket)}")

        # Jones polynomial: J(t) = (-A^3)^{-w} * <D>, then A^2 = t^{-1/2}
        # Normalized: multiply by (-A^3)^{-w}
        if w != 0:
            norm_factor = {}
            norm_power = -3 * w
            norm_sign = (-1)**abs(w) if w % 2 != 0 else 1
            norm_factor[norm_power] = norm_sign
            jones = _poly_mul(bracket, norm_factor)
            print(f"    (-A³)^{{-w}} ⟨D⟩ = {format_poly(jones)}")
        print()

    # ── Effect of smoothing crossings ���─

    print("═══════════════════════════════════════════════════════")
    print("  Effect of smoothing: crossing → smooth at each cell")
    print("══════════════════════════════════���════════════════════")
    print()

    rows, cols = 3, 3
    grid_all_cross = all_cross_grid(rows, cols)
    nc_base = count_components(grid_all_cross, rows, cols)
    print(f"  3×3 torus, all crossings: {nc_base} components")
    print()

    # Smooth one crossing at a time
    print("  Smoothing one crossing:")
    for r in range(rows):
        for c in range(cols):
            for smooth_type, smooth_name in [(SMOOTH_A, 'A'), (SMOOTH_B, 'B')]:
                grid = [row[:] for row in grid_all_cross]
                grid[r][c] = smooth_type
                nc = count_components(grid, rows, cols)
                delta = nc - nc_base
                print(f"    ({r},{c})→{smooth_name}: {nc} components (Δ={delta:+d})")
        if r < rows - 1:
            print()

    # ── Relationship between smoothing pattern and number of components ──

    print()
    print("═══════════════════════════════════════════════════════")
    print("  Smoothing patterns ↔ components: the TL connection")
    print("══════════════��════════════════════════════════════════")
    print()

    rows, cols = 2, 2
    print(f"  {rows}×{cols} torus: smoothing all {rows*cols} crossings in all 2^{rows*cols} ways")
    print()
    print(f"  {'Smoothing':>12}  {'Components':>10}  {'d^(c-1)':>10}")
    print(f"  {'─'*12}  {'─'*10}  {'─'*10}")

    for smoothing in iproduct(['A', 'B'], repeat=rows*cols):
        grid = all_cross_grid(rows, cols)
        for idx, s in enumerate(smoothing):
            r, c = divmod(idx, cols)
            grid[r][c] = SMOOTH_A if s == 'A' else SMOOTH_B
        nc = count_components(grid, rows, cols)
        label = ''.join(smoothing)
        print(f"  {label:>12}  {nc:>10}  d^{nc-1}")

    print()
    print("  This is the TL trace! Each smoothing gives d^{loops-1}")
    print("  where d = -A² - A⁻². The Kauffman bracket sums these.")
    print()

    # ── Connection to maze tiles ──

    print("═══════════════════════════════════════════════════════")
    print("  Connection to maze tiles")
    print("═��══════════════��════════════════════════════���═════════")
    print()
    print("  Maze tile     ↔  Knot tile     ↔  TL algebra")
    print("  ─────────────────────────────────────────────────")
    print("  Corner (└ ┐)  ↔  Smooth A/B    ↔  TL generator eᵢ")
    print("  Straight (│─) ↔  Smooth A/B    ↔  TL generator eᵢ")
    print("  Crossing (╳)  ↔  Crossing      ↔  Identity I")
    print("  T-junction    ↔  (no analogue)  ↔  (branching)")
    print("  Dead end      ↔  (no analogue)  ↔  (endpoint)")
    print()
    print("  The maze tile with NO branching (degree-2 tiles only)")
    print("  = a smoothing of the all-crossings Celtic knot pattern.")
    print("  Each smoothing pattern = a collection of closed loops.")
    print()
    print("  Maze (spanning tree) tiles BRANCH → not a knot.")
    print("  Knotted maze = tree skeleton + crossings on non-tree edges.")
    print("  The crossings live WHERE THE MAZE HAS WALLS.")
    print()

    # ── Random knotted mazes ──

    print("═══════════════════════════════════════════════════════")
    print("  Random knotted mazes on torus")
    print("═════════════════════════════════════════════���═════════")
    print()

    rng = np.random.default_rng(42)
    for rows, cols in [(4, 4), (6, 6), (8, 8)]:
        comp_dist = Counter()
        n_samples = 10000
        for _ in range(n_samples):
            grid = random_grid(rows, cols, cross_prob=0.5, rng=rng)
            nc = count_components(grid, rows, cols)
            comp_dist[nc] += 1

        mean_comp = sum(nc * count for nc, count in comp_dist.items()) / n_samples
        print(f"  {rows}×{cols} torus (p_cross=0.5, {n_samples} samples):")
        print(f"    Mean components: {mean_comp:.2f}")
        top = sorted(comp_dist.items(), key=lambda x: -x[1])[:5]
        for nc, count in top:
            print(f"      {nc} components: {count:>5} ({100*count/n_samples:.1f}%)")
        print()
