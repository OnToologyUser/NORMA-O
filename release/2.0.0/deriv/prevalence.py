"""Evaluation of the defeat digraph.

Pieces kept apart on purpose, because they answer different questions:

  kahn()      layered topological order, and along the way the set of nodes
              that admit no order, which is the CYCLE DETECTION the layer
              calls for.
  sccs()      all strongly connected components (Kosaraju).
  cycles()    only the non-trivial components, so that each cycle can be
              REPORTED instead of merely saying one exists.
  strata()    the published levels, computed on the condensation so that
              every norm gets a rung.
  grounded()  Dung's grounded labelling, which is what provides reinstatement.

The labelling does NOT rely on the topological order. A single pass in
topological order goes wrong downstream of a cycle: if c is in force and
withdraws both nodes of a cycle a <-> a', and a attacks b, then b stays in force
because its only attacker is withdrawn, and a single pass would leave it
undecided. The monotone fixpoint is used instead: it grows the "in force" and
"withdrawn" sets until they stabilise and leaves undecided only what the
asserted edges do not settle.
"""

# The labels are about APPLICABILITY to the case, not validity: validity is
# settled by the lifecycle status and by temporal defeat, before reaching here.
APPLICABLE, DEFEATED, UNDECIDED = "Applicable", "Defeated", "Undecided"


def _attackers(nodes, edges):
    att = {n: set() for n in nodes}
    for a, b in edges:
        if a in att and b in att:
            att[b].add(a)
    return att


def kahn(nodes, edges):
    """Layered topological order. Returns (order, levels, remainder).

    level(n) = 0 if nothing defeats n, otherwise one more than the maximum
    level of the norms that defeat it: longest-path layering, so the level is
    canonical for a given digraph. The remainder is the nodes that lie on a
    cycle or downstream of one, for which kahn() defines no level (strata()
    does, on the condensation).
    """
    nodes = list(nodes)
    out = {n: set() for n in nodes}
    for a, b in edges:
        if a in out and b in out:
            out[a].add(b)
    indeg = {n: len(a) for n, a in _attackers(nodes, edges).items()}
    level = {n: 0 for n in nodes}
    queue = sorted((n for n in nodes if indeg[n] == 0), key=str)
    order = []
    while queue:
        n = queue.pop(0)
        order.append(n)
        for m in sorted(out[n], key=str):
            level[m] = max(level[m], level[n] + 1)
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)
        queue.sort(key=str)
    seen = set(order)
    return order, {n: level[n] for n in order}, [n for n in nodes if n not in seen]


def sccs(nodes, edges):
    """ALL strongly connected components, by iterative Kosaraju.

    They are returned in topological order of the reversed condensation, which
    is the reversed post-order of the first pass; each component is sorted.
    Returns (components, nodes_with_a_self_loop).
    """
    nodes = list(nodes)
    idx = set(nodes)
    fwd, rev = {n: set() for n in nodes}, {n: set() for n in nodes}
    loops = set()
    for a, b in edges:
        if a in idx and b in idx:
            if a == b:
                loops.add(a)
            fwd[a].add(b)
            rev[b].add(a)

    visited, post = set(), []
    for root in sorted(nodes, key=str):                 # first pass: post-order
        if root in visited:
            continue
        stack = [(root, iter(sorted(fwd[root], key=str)))]
        visited.add(root)
        while stack:
            n, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                post.append(n)
                stack.pop()
            elif nxt not in visited:
                visited.add(nxt)
                stack.append((nxt, iter(sorted(fwd[nxt], key=str))))

    assigned, comps = set(), []
    for root in reversed(post):                         # second pass, over the reverse
        if root in assigned:
            continue
        comp, stack = [], [root]
        assigned.add(root)
        while stack:
            n = stack.pop()
            comp.append(n)
            for m in sorted(rev[n], key=str):
                if m not in assigned:
                    assigned.add(m)
                    stack.append(m)
        comps.append(sorted(comp, key=str))
    return comps, loops


def cycles(nodes, edges):
    """Only the NON-TRIVIAL components: cycles proper.

    A node downstream of a cycle is in Kahn's remainder but in no component of
    more than one node, so it is not reported as a cycle: it is not one.
    """
    comps, loops = sccs(nodes, edges)
    return [c for c in comps if len(c) > 1 or c[0] in loops]


def strata(nodes, edges):
    """Levels over the CONDENSATION into strongly connected components.

    Kahn alone is not enough for the levels: since it cannot peel a cycle, it
    cannot peel anything that depends on one either, so the ACYCLIC
    descendants of a cycle would be left without a level even though their
    place on the ladder is fully determined. Contracting each component to a
    node yields a digraph that is always acyclic, so it is stratified entirely,
    and the norms of one cycle share the rung of their component.

    Returns (levels, non_trivial_components, nodes_on_a_cycle).
    """
    nodes = list(nodes)
    comps, loops = sccs(nodes, edges)
    comp_of = {n: i for i, c in enumerate(comps) for n in c}
    cedges = {(comp_of[a], comp_of[b]) for a, b in edges
              if a in comp_of and b in comp_of and comp_of[a] != comp_of[b]}
    _, clevels, crest = kahn(range(len(comps)), cedges)
    assert not crest, "the condensation cannot have cycles"
    nontrivial = [c for c in comps if len(c) > 1 or c[0] in loops]
    cyclic = {n for c in nontrivial for n in c}
    return {n: clevels[comp_of[n]] for n in nodes}, nontrivial, cyclic


def grounded(nodes, edges, strict=frozenset()):
    """Grounded labelling: the unique minimal complete labelling.

    A Strict norm admits no defeat, so its incoming edges are removed before
    evaluating; it stays applicable and cannot drag anything down.

    Being on a cycle does NOT imply being undecided: if a and b defeat each
    other and an undefeated c defeats a, the fixpoint gives c applicable, a
    defeated and b APPLICABLE, because b is reinstated when its only attacker
    falls. Conversely, a norm outside every cycle whose attackers are
    undecided is itself undecided. The label follows the fixpoint, not
    membership of a cycle.
    """
    nodes = list(nodes)
    edges = {(a, b) for a, b in edges if b not in strict}
    att = _attackers(nodes, edges)
    inf, wd = set(), set()
    changed = True
    while changed:                                      # monotone: only grows
        changed = False
        for n in nodes:
            if n in inf or n in wd:
                continue
            if att[n] <= wd:                            # all withdrawn, or none
                inf.add(n)
                changed = True
            elif att[n] & inf:                          # some attacker in force
                wd.add(n)
                changed = True
    return {n: APPLICABLE if n in inf else DEFEATED if n in wd else UNDECIDED
            for n in nodes}
