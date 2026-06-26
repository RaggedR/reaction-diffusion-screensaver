#!/usr/bin/env python3
"""Enumerate valid connected Penrose P2 (kite/dart) patches by tile composition."""

import math
from collections import defaultdict
import time

PHI = (1 + math.sqrt(5)) / 2
A36 = math.pi / 5
LONG = PHI
SHORT = 1.0
GRID = 0.01

def sn(x):
    return round(x / GRID) * GRID

def make_verts(tt, tip, ai):
    axis = ai * A36
    tx, ty = tip
    B = (tx + LONG*math.cos(axis+A36), ty + LONG*math.sin(axis+A36))
    D = (tx + LONG*math.cos(axis-A36), ty + LONG*math.sin(axis-A36))
    r = LONG if tt == 'K' else SHORT
    C = (tx + r*math.cos(axis), ty + r*math.sin(axis))
    return [(tx,ty), B, C, D]

def centroid(vs):
    return (sum(v[0] for v in vs)/len(vs), sum(v[1] for v in vs)/len(vs))

def pt_in_poly(px, py, vs):
    inside = False
    n = len(vs)
    j = n - 1
    for i in range(n):
        xi, yi = vs[i]; xj, yj = vs[j]
        if ((yi > py) != (yj > py)) and (px < (xj-xi)*(py-yi)/(yj-yi)+xi):
            inside = not inside
        j = i
    return inside

def shrink(vs, amt):
    cx, cy = centroid(vs)
    return [(v[0]+(cx-v[0])*amt, v[1]+(cy-v[1])*amt) for v in vs]

def cross2(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])

def tiles_overlap(vA, vB):
    EPS = 0.5
    sA, sB = shrink(vA, 0.03), shrink(vB, 0.03)
    cA, cB = centroid(vA), centroid(vB)
    if pt_in_poly(cA[0], cA[1], sB): return True
    if pt_in_poly(cB[0], cB[1], sA): return True
    for v in vA:
        if pt_in_poly(v[0], v[1], sB): return True
    for v in vB:
        if pt_in_poly(v[0], v[1], sA): return True
    for i in range(4):
        mx = (vA[i][0]+vA[(i+1)%4][0])/2; my = (vA[i][1]+vA[(i+1)%4][1])/2
        if pt_in_poly(mx, my, sB): return True
        mx = (vB[i][0]+vB[(i+1)%4][0])/2; my = (vB[i][1]+vB[(i+1)%4][1])/2
        if pt_in_poly(mx, my, sA): return True
    for i in range(4):
        for j in range(4):
            p1,p2 = vA[i],vA[(i+1)%4]; p3,p4 = vB[j],vB[(j+1)%4]
            d1,d2 = cross2(p3,p4,p1),cross2(p3,p4,p2)
            d3,d4 = cross2(p1,p2,p3),cross2(p1,p2,p4)
            if ((d1>EPS and d2<-EPS) or (d1<-EPS and d2>EPS)) and \
               ((d3>EPS and d4<-EPS) or (d3<-EPS and d4>EPS)):
                return True
    return False

# ─── Matching rules ────────────────────────────────
VTX_MARKS = [True, True, False, True]
CHIRALITY = {'K': {0:'a', 3:'A'}, 'D': {0:'A', 3:'a'}}

def edges_ok(st, se, nt, ne):
    if VTX_MARKS[se] != VTX_MARKS[(ne+1)%4]: return False
    if VTX_MARKS[(se+1)%4] != VTX_MARKS[ne]: return False
    s = CHIRALITY[st].get(se); n = CHIRALITY[nt].get(ne)
    if s and n: return s != n
    return True

def dist(a, b):
    return math.hypot(b[0]-a[0], b[1]-a[1])

def edge_key(p, q):
    pk = (sn(p[0]), sn(p[1])); qk = (sn(q[0]), sn(q[1]))
    return (min(pk,qk), max(pk,qk))

def check_all_shared_edges(nt, new_verts, tiles, all_verts):
    """Check matching rules on ALL edges shared with existing tiles, not just attachment edge."""
    for ti, (et, etx, ety, eai) in enumerate(tiles):
        ev = all_verts[ti]
        for nei in range(4):
            for eei in range(4):
                nP, nQ = new_verts[nei], new_verts[(nei+1)%4]
                eP, eQ = ev[eei], ev[(eei+1)%4]
                # Edges coincide if reversed: nP≈eQ and nQ≈eP
                if (abs(nP[0]-eQ[0])<0.1 and abs(nP[1]-eQ[1])<0.1 and
                    abs(nQ[0]-eP[0])<0.1 and abs(nQ[1]-eP[1])<0.1):
                    if not edges_ok(et, eei, nt, nei):
                        return False
    return True

# ─── Exposed edges ──────────────────────────────────
def get_exposed(tiles, all_verts):
    ec = defaultdict(list)
    for ti, (tt, tx, ty, ai) in enumerate(tiles):
        vs = all_verts[ti]
        for ei in range(4):
            ek = edge_key(vs[ei], vs[(ei+1)%4])
            ec[ek].append((vs[ei], vs[(ei+1)%4], tt, ei))
    return [entries[0] for entries in ec.values() if len(entries) == 1]

# ─── Find valid extensions ─────────────────────────
def find_extensions(tiles, all_verts):
    exposed = get_exposed(tiles, all_verts)
    results = []
    seen = set()

    for P, Q, st, se in exposed:
        elen = dist(P, Q)
        is_long = abs(elen - LONG) < 0.1

        for nt in ['K', 'D']:
            for ne in range(4):
                if is_long and ne not in (0,3): continue
                if not is_long and ne not in (1,2): continue
                if not edges_ok(st, se, nt, ne): continue

                for ai in range(10):
                    vo = make_verts(nt, (0,0), ai)
                    tip = (Q[0]-vo[ne][0], Q[1]-vo[ne][1])
                    vs = make_verts(nt, tip, ai)
                    nxt = (ne+1)%4
                    if abs(vs[nxt][0]-P[0])>0.1 or abs(vs[nxt][1]-P[1])>0.1:
                        continue

                    tk = (nt, sn(tip[0]), sn(tip[1]), ai)
                    if tk in seen: continue
                    seen.add(tk)

                    # Not duplicate of existing tile
                    dup = False
                    for et in tiles:
                        if et[0]==nt and abs(et[1]-tip[0])<0.1 and abs(et[2]-tip[1])<0.1 and et[3]==ai:
                            dup = True; break
                    if dup: continue

                    # Check ALL shared edges satisfy matching rules
                    if not check_all_shared_edges(nt, vs, tiles, all_verts):
                        continue

                    # Check overlap
                    ok = True
                    for ev in all_verts:
                        if tiles_overlap(vs, ev):
                            ok = False; break
                    if ok:
                        results.append((nt, tip[0], tip[1], ai))
    return results

# ─── Canonical form under dihedral group of order 20 ──
def canonical(tiles):
    if not tiles: return ()
    best = None
    for refl in [False, True]:
        for rot in range(10):
            angle = rot * A36
            ca, sa = math.cos(angle), math.sin(angle)
            transformed = []
            for tt, tx, ty, ai in tiles:
                if refl:
                    x, y, a = tx, -ty, (-ai) % 10
                else:
                    x, y, a = tx, ty, ai
                rx = x*ca - y*sa
                ry = x*sa + y*ca
                a = (a + rot) % 10
                transformed.append((tt, sn(rx), sn(ry), a))
            mx = min(t[1] for t in transformed)
            my = min(t[2] for t in transformed)
            norm = tuple(sorted((t[0], sn(t[1]-mx), sn(t[2]-my), t[3]) for t in transformed))
            if best is None or norm < best:
                best = norm
    return best

# ─── BFS enumeration ────────────────────────────────
def enumerate_patches(max_k, max_d):
    target = max_k + max_d
    t0 = time.time()

    # Seed: one kite, one dart (axis=0, at origin)
    layer = {}
    for tt in ['K', 'D']:
        tiles = [(tt, 0.0, 0.0, 0)]
        verts = [make_verts(tt, (0,0), 0)]
        cf = canonical(tiles)
        layer[cf] = (tiles, verts)

    all_seen = set(layer.keys())
    counts = defaultdict(set)
    for cf, (tiles, _) in layer.items():
        k = sum(1 for t in tiles if t[0]=='K')
        d = sum(1 for t in tiles if t[0]=='D')
        counts[(k,d)].add(cf)

    print(f"Size  1: {len(layer):>5} patches  ({time.time()-t0:.1f}s)")

    for size in range(2, target+1):
        new_layer = {}
        for cf, (tiles, verts) in layer.items():
            exts = find_extensions(tiles, verts)
            for nt, tx, ty, ai in exts:
                new_tiles = tiles + [(nt, tx, ty, ai)]
                nk = sum(1 for t in new_tiles if t[0]=='K')
                nd = sum(1 for t in new_tiles if t[0]=='D')
                if nk > max_k or nd > max_d: continue

                new_verts = verts + [make_verts(nt, (tx,ty), ai)]
                ncf = canonical(new_tiles)
                if ncf not in all_seen:
                    new_layer[ncf] = (new_tiles, new_verts)
                    all_seen.add(ncf)
                    counts[(nk,nd)].add(ncf)

        layer = new_layer
        print(f"Size {size:>2}: {len(layer):>5} patches  ({time.time()-t0:.1f}s)")
        if not layer:
            print("No new patches found, stopping.")
            break

    return counts

# ─── Run ─────────────────────────────────────────────
results = enumerate_patches(8, 5)

print(f"\n{'Kites':>6} {'Darts':>6} {'Count':>7} {'K/D':>8}")
print("─" * 32)
for (k,d) in sorted(results.keys()):
    c = len(results[(k,d)])
    r = f"{k/d:.3f}" if d > 0 else "  inf"
    print(f"{k:>6} {d:>6} {c:>7} {r:>8}")

target = results.get((8,5), set())
print(f"\n★ Patches with 8 kites + 5 darts (up to isometry): {len(target)}")
