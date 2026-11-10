#!/usr/bin/env python3
"""Checks for the reference rule set: deontic closure, weak permission,
Hohfeldian positions, norm-to-norm relations, prevalence ordering, roles, the
OWL 2 DL profile and consistency.

Deliberately not named test_*.py: it is a standalone script, not a pytest
module. Requires rdflib, and owlready2 (with Java, for HermiT).

  python deriv/tests/check_deriv.py
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from rdflib import Graph, Namespace, RDF, URIRef
from rdflib.namespace import OWL, RDFS

N = Namespace("https://w3id.org/def/norma-o#")
T = Namespace("https://example.org/norma-test#")
# the ontology folder (the one that contains deriv/), not the repository root
ONTO = Path(__file__).resolve().parent.parent.parent
ABOX = ONTO / "deriv" / "tests" / "test-abox.ttl"
P = {k: N[v] for k, v in {"O": "entailsObligatory", "NO": "entailsNotObligatory",
     "P": "entailsPermitted", "NP": "entailsNotPermitted", "F": "entailsForbidden",
     "NF": "entailsNotForbidden", "Rec": "entailsRecommended", "NegRec": "entailsDiscouraged"}.items()}

fails = []
def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + ("" if cond else f"  <- {detail}"))
    if not cond: fails.append(name)

def run(out):
    subprocess.run([sys.executable, str(ONTO / "deriv" / "derive.py"), str(ABOX),
                    "-o", out], check=True, capture_output=True)
    return Graph().parse(out, format="turtle")

tmp = tempfile.mkdtemp()
g_open = run(f"{tmp}/open.ttl")

# ── 1. exact closure: nothing missing, nothing extra ────────────────
EXPECT = {
 "n_obl":  {("O","act_o"),("P","act_o"),("NF","act_o"),("F","act_o_neg"),("NP","act_o_neg"),("NO","act_o_neg")},
 "n_prh":  {("F","act_f"),("NP","act_f"),("NO","act_f"),("O","act_f_neg"),("P","act_f_neg"),("NF","act_f_neg")},
 "n_per":  {("P","act_p"),("NF","act_p"),("NO","act_p_neg")},
 "n_fac":  {("P","act_fa"),("NF","act_fa"),("NO","act_fa_neg"),("P","act_fa_neg"),("NF","act_fa_neg"),("NO","act_fa")},
 "n_rec":  {("Rec","act_r"),("NegRec","act_r_neg")},
 "n_nrec": {("NegRec","act_nr"),("Rec","act_nr_neg")},
 "n_fct":  set(),
}
inv = {v: k for k, v in P.items()}
for norm, exp in EXPECT.items():
    got = {(inv[p], str(o).split("#")[-1]) for p, o in g_open.predicate_objects(T[norm]) if p in inv}
    check(f"exact closure of {norm}", got == exp, f"extra {got-exp} missing {exp-got}")

# ── 2. weak permission cases ─────────────────────────────────────────
def wp(g, agent, action, case):
    return any(g.value(w, N.aboutAction) == T[action] and g.value(w, N.forAgent) == T[agent]
               and g.value(w, N.inFactPattern) == T[case]
               for w in g.subjects(RDF.type, N.WeakPermission))
cases = ["C1", "C2", "C3"]
check("T1: no WP(A,b,C1) — prohibition activated in C1", not wp(g_open,"A","b","C1"))
check("T2: WP(A,b,C2) — prohibition not activated in C2", wp(g_open,"A","b","C2"))
check("T3: WP(A,b,C3) — condition not activated in C3", wp(g_open,"A","b","C3"))
check("T4: no WP(A,d,·) at all — unconditional prohibition", not any(wp(g_open,"A","d",c) for c in cases))
check("T5: WP(A,e,·) in every case (superseded norm)", all(wp(g_open,"A","e",c) for c in cases))
check("T6: no WP(A,g_neg,·)", not any(wp(g_open,"A","g_neg",c) for c in cases))
check("T6: WP(A,g,·) present", all(wp(g_open,"A","g",c) for c in cases))
check("T7: WP(B,b,·) even though it is forbidden to A", all(wp(g_open,"B","b",c) for c in cases))
check("T8: WP(A,h,C1) — the prohibition is defeated in C1", wp(g_open,"A","h","C1"))
check("T9: no WP(A,h,C2/C3) — the defeater is not active", not wp(g_open,"A","h","C2") and not wp(g_open,"A","h","C3"))
check("T10: WP(A,k_neg,C1) — undercutting the obligation weakly permits the omission", wp(g_open,"A","k_neg","C1"))
check("T10: no WP(A,k_neg,C2/C3) — the obligation still stands", not wp(g_open,"A","k_neg","C2") and not wp(g_open,"A","k_neg","C3"))
check("T11: no WP(A,m_neg,C1) — n_m is REINSTATED, because its defeater "
      "fct_chain is itself defeated by fct_exc (what a flat filter cannot see)",
      not wp(g_open,"A","m_neg","C1"))

# ── 2d. prevalence ladder, Kahn and grounded semantics ──────────────
ND = Namespace("https://w3id.org/def/norma-o/deriv#")
def ordering(g, case=None):
    for o in g.subjects(RDF.type, ND.PrevalenceOrdering):
        fp = g.value(o, ND.forFactPattern)
        if (case is None and fp is None) or (case is not None and fp == T[case]):
            return o
    return None
def evals(g, o):
    out = {}
    for ev in g.subjects(ND.inOrdering, o):
        n = str(g.value(ev, ND.evaluatedNorm)).split("#")[-1]
        lv = g.value(ev, ND.prevalenceLevel)
        st = g.value(ev, ND.hasApplicabilityStatus)
        out[n] = (int(lv) if lv is not None else None,
                  str(st).split("#")[-1] if st is not None else None)
    return out

STAT = evals(g_open, ordering(g_open))
C1 = evals(g_open, ordering(g_open, "C1"))
C2 = evals(g_open, ordering(g_open, "C2"))

check("D1: the static ladder exists and does not decide cases (level yes, status no)",
      STAT and all(st is None for _, st in STAT.values()))
check("D2: the chain fct_exc -> fct_chain -> n_m gives three strata",
      (STAT["fct_exc"][0], STAT["fct_chain"][0], STAT["n_m"][0]) == (0, 1, 2))
check("D3: a norm that nothing defeats is at level 0",
      STAT["n_obl"][0] == 0 and STAT["n_fac"][0] == 0)
check("D4: the ladder of the main fixture is ACYCLIC",
      g_open.value(ordering(g_open), ND.isAcyclic).toPython() is True)
check("D5: REINSTATEMENT — in C1 fct_chain is withdrawn and n_m IN FORCE",
      C1["fct_chain"][1] == "Defeated" and C1["n_m"][1] == "Applicable")
check("D6: in C1 the defeater fct_exc is in force (nothing defeats it)",
      C1["fct_exc"][1] == "Applicable")
check("D7: one-level defeat in C1: n_h and n_k withdrawn",
      C1["n_h"][1] == "Defeated" and C1["n_k"][1] == "Defeated")
check("D8: defeat is RELATIVE TO THE CASE: in C2 the gate te_x_true "
      "does not fire, so n_h stays in force",
      C2["n_h"][1] == "Applicable")
check("D9: the Superseded norm is OUTSIDE the static ladder (it is not part "
      "of the system being stratified) but the case reports it as Invalid, "
      "so it is not mistaken for a norm absent from the graph",
      "n_e" not in STAT and C1["n_e"] == (None, "Invalid"))
check("D10: every norm gets a status in every case", all(st for _, st in C1.values()))
check("D12: NotActivated is distinct from Defeated — in C2 the true branch of "
      "c1 does not fire, so n_b is not triggered rather than defeated",
      C2["n_b"][1] == "NotActivated")
check("D13: a norm with no condition is unconditional and never NotActivated",
      C1["n_obl"][1] == "Applicable" and C2["n_obl"][1] == "Applicable")
check("D14: Invalid does not depend on the case",
      all(evals(g_open, ordering(g_open, c))["n_e"][1] == "Invalid"
          for c in ("C1", "C2", "C3")))
check("P1: ACTIVATION filters the ATTACK GRAPH, not just the report. "
      "The defeater's gate fires in C1, but the excepting norm is not "
      "activated, so it is not operative and does NOT defeat",
      C1["fct_p1"][1] == "NotActivated" and C1["n_p1"][1] == "Applicable")
check("P2: a REPEALED exception does not defeat (n_p2 recovers nothing: "
      "it never lost its validity)",
      C1["fct_p2"][1] == "Invalid" and C1["n_p2"][1] == "Applicable")
check("P3: legitimate defeat still works, so P1/P2 are not "
      "a filter that disables everything",
      C1["n_h"][1] == "Defeated")
check("P4: gate and activation are read CONJUNCTIVELY: with the gate "
      "fired and the norm activated, the defeat does happen",
      C1["fct_exc"][1] == "Applicable" and C1["n_k"][1] == "Defeated")
check("D11: the status is reified per case, not on the norm "
      "(n_h differs between C1 and C2)",
      C1["n_h"][1] != C2["n_h"][1])

# ── 2b. Hohfeldian positions derived from the closure ───────────────
def positions(g, cls, norm):
    return [p for p in g.subjects(RDF.type, N[cls]) if f"#{norm}_" in str(p)]
def content(g, p): return str(g.value(p, N.concernsLegalAction)).split("#")[-1]

duty_obl = positions(g_open, "Duty", "n_obl")
check("H1: the obligation confers ONE duty over the annotated action",
      len(duty_obl) == 1 and content(g_open, duty_obl[0]) == "act_o")
check("H1: holder of the duty = agent of the norm",
      g_open.value(duty_obl[0], N.hasPositionHolder) == T["A"])
duty_prh = positions(g_open, "Duty", "n_prh")
check("H2: the prohibition confers a duty over the NEGATED action",
      len(duty_prh) == 1 and content(g_open, duty_prh[0]) == "act_f_neg",
      content(g_open, duty_prh[0]) if duty_prh else "no duty")
privs_fac = sorted(content(g_open, p) for p in positions(g_open, "Privilege", "n_fac"))
check("H3: the facultative norm confers TWO privileges, over x and over ¬x",
      privs_fac == ["act_fa", "act_fa_neg"], str(privs_fac))
check("H4: a plain permission confers ONE privilege",
      len(positions(g_open, "Privilege", "n_per")) == 1)
check("H5: the obligation confers NO privilege (no noise from axiom D)",
      len(positions(g_open, "Privilege", "n_obl")) == 0)
check("H6: the recommendation confers no position",
      all(len(positions(g_open, cl, "n_rec")) == 0 for cl in ("Duty","Claim","Privilege","NoRight")))
check("H7: no derived position is left without a holder",
      not [p for cl in ("Duty","Claim","Privilege","NoRight") for p in g_open.subjects(RDF.type, N[cl])
           if not g_open.value(p, N.hasPositionHolder)])
check("H8: correlative only if the norm names a counterparty",
      len(positions(g_open, "Claim", "n_obl")) == 1 and len(positions(g_open, "Claim", "n_prh")) == 0)
check("H9: the correlative's content is NOT materialised (it propagates through the chain)",
      g_open.value(positions(g_open, "Claim", "n_obl")[0], N.concernsLegalAction) is None)

# ── 2a-bis. jural opposites (stage 4c/4d) ───────────────────────────
def opp_pairs():
    return {frozenset((a, b)) for a, b in g_open.subject_objects(N.isJuralOppositeOf)}
def cls_of(p):
    return {str(c).split("#")[-1] for c in g_open.objects(p, RDF.type)}

J1 = frozenset((positions(g_open, "Duty", "n_q_prh")[0],
                positions(g_open, "Privilege", "n_q_per")[0]))
check("J1: Duty(A,q2_neg) and Privilege(A,q2) are jural OPPOSITES", J1 in opp_pairs())
check("J2: the opposition is mirrored on the correlatives Claim <-> NoRight",
      frozenset((positions(g_open, "Claim", "n_q_prh")[0],
                 positions(g_open, "NoRight", "n_q_per")[0])) in opp_pairs())
check("J3: the CONTRARY pair produces no jural opposition "
      "(two Duties, not Duty against Privilege)",
      not [p for p in opp_pairs()
           if p & set(positions(g_open, "Duty", "n_r_obl"))])
check("J4: same negated content but different HOLDERS are not opposites "
      "(n_b forbids b to A, n_b_B permits it to B)",
      not [p for p in opp_pairs()
           if p & set(positions(g_open, "Duty", "n_b"))])
check("J5: opposition only crosses one axis of the square",
      all(cls_of(a) & {"Duty", "Claim"} and cls_of(b) & {"Privilege", "NoRight"}
          or cls_of(b) & {"Duty", "Claim"} and cls_of(a) & {"Privilege", "NoRight"}
          for a, b in (tuple(p) for p in opp_pairs())))
check("J6: no position is its own opposite",
      not [a for a, b in g_open.subject_objects(N.isJuralOppositeOf) if a == b])
check("J7: opposition comes out symmetric",
      all((o, N.isJuralOppositeOf, su) in g_open
          for su, o in g_open.subject_objects(N.isJuralOppositeOf)))
check("J8: THE TWO ROUTES AGREE — if two positions from different norms are "
      "opposites, those norms are in deonticallyConflictsWith",
      all((n1, N.deonticallyConflictsWith, n2) in g_open
          for a, b in (tuple(p) for p in opp_pairs())
          for n1 in g_open.subjects(N.confersLegalPosition, a)
          for n2 in g_open.subjects(N.confersLegalPosition, b)
          if n1 != n2))

# ── 2b. norm-to-norm relations (stage 5) ────────────────────────────
def rel(prop, a, b):
    return (T[a], N[prop], T[b]) in g_open
def rel_sym(prop, a, b):
    return rel(prop, a, b) and rel(prop, b, a)

check("E1: F(¬x) ≡ O(x) — identical closures, in both directions",
      rel_sym("isDeonticallyEquivalentTo", "n_eq_obl", "n_eq_prh"))
check("E2: a different counterparty breaks equivalence",
      not rel("isDeonticallyEquivalentTo", "n_eq_obl", "n_eq_obl_C")
      and not rel("isDeonticallyEquivalentTo", "n_eq_prh", "n_eq_obl_C"))
check("E3: a different agent breaks equivalence",
      not rel("isDeonticallyEquivalentTo", "n_eq_obl", "n_eq_obl_B"))
check("E4: Permission and Facultative over the same action are NOT equivalent "
      "(a single-triple join would merge them)",
      not rel("isDeonticallyEquivalentTo", "n_p2_per", "n_p2_fac"))
check("E4: and yet they share entailsPermitted(p2)",
      (T["n_p2_per"], N.entailsPermitted, T["p2"]) in g_open
      and (T["n_p2_fac"], N.entailsPermitted, T["p2"]) in g_open)
check("E5: P(q2) and F(q2) are CONTRADICTORY, in both directions",
      rel_sym("deonticallyContradicts", "n_q_per", "n_q_prh"))
check("E5: the contradiction also materialises the superproperty",
      rel_sym("deonticallyConflictsWith", "n_q_per", "n_q_prh"))
check("E6: O(r2) and F(r2) are CONTRARY: conflict yes, contradiction no",
      rel_sym("deonticallyConflictsWith", "n_r_obl", "n_r_prh")
      and not rel("deonticallyContradicts", "n_r_obl", "n_r_prh")
      and not rel("deonticallyContradicts", "n_r_prh", "n_r_obl"))
check("E7: the activation condition matters — n_obl and n_other share a "
      "closure but only one is conditional",
      not rel("isDeonticallyEquivalentTo", "n_obl", "n_other"))
check("E11: MULTITAL — Duty(A->B, mt) and Privilege(A->C, ¬mt) are NOT jural "
      "opposites: same holder and negated contents, but different counterparties, "
      "so they are two distinct jural relations",
      not [p for p in {frozenset(q) for q in
                       g_open.subject_objects(N.isJuralOppositeOf)}
           if p & set(positions(g_open, "Duty", "n_mt_d"))])
check("J9: jural opposition also filters INCOMPATIBLE conditions, "
      "like 05b: n_cc_obl and n_cc_prh are on opposite branches of c2",
      not [p for p in {frozenset(q) for q in
                       g_open.subject_objects(N.isJuralOppositeOf)}
           if p & set(positions(g_open, "Duty", "n_cc_obl"))])
check("J10: THE TWO ROUTES AGREE in the other direction — if there is no "
      "deontic contradiction between two norms, there is no opposition "
      "between their positions either",
      all((n1, N.deonticallyConflictsWith, n2) in g_open
          for a, b in ({frozenset(q) for q in
                        g_open.subject_objects(N.isJuralOppositeOf)})
          for n1 in g_open.subjects(N.confersLegalPosition, a)
          for n2 in g_open.subjects(N.confersLegalPosition, b)
          if n1 != n2))
check("E12: INCOMPATIBLE CONDITIONS — O(cc) under c2 true and F(cc) under c2 "
      "false do not conflict: they never coincide in a case",
      not rel("deonticallyConflictsWith", "n_cc_obl", "n_cc_prh")
      and not rel("deonticallyConflictsWith", "n_cc_prh", "n_cc_obl"))
check("E13: and yet the contrariety through the closure IS there "
      "(O(cc) and F(cc)), so it is the condition filter that discards it",
      (T["n_cc_obl"], N.entailsObligatory, T["cc"]) in g_open
      and (T["n_cc_prh"], N.entailsForbidden, T["cc"]) in g_open)
check("E14: the contrary pair WITHOUT conditions is still reported",
      rel_sym("deonticallyConflictsWith", "n_r_obl", "n_r_prh"))
check("E8: no norm is equivalent to, contradicts or conflicts with itself",
      not [n for p in ("isDeonticallyEquivalentTo", "deonticallyContradicts",
                       "deonticallyConflictsWith")
           for n, m in g_open.subject_objects(N[p]) if n == m])
check("E9: the three relations always come out symmetric",
      all((o, N[p], su) in g_open
          for p in ("isDeonticallyEquivalentTo", "deonticallyContradicts",
                    "deonticallyConflictsWith")
          for su, o in g_open.subject_objects(N[p])))
check("E10: no constitutive rule takes part in an equivalence",
      not [n for n, _ in g_open.subject_objects(N.isDeonticallyEquivalentTo)
           if (n, RDF.type, N.ConstitutiveRule) in Graph().parse(ABOX, format="turtle")])

# ── 2c. OWL 2 DL global restriction: only SIMPLE properties ──────────
# A property is NON-simple if it is transitive, defined by a chain, or has a
# non-simple subproperty. OWL 2 DL forbids declaring a non-simple property
# functional, inverse functional, irreflexive, asymmetric or disjoint, and
# forbids using it in cardinality restrictions. This is checked here and not
# only through HermiT, because a reasoner may silently accept a file outside
# the profile.
tbox = Graph().parse(ONTO/"norma-ontology-v2.ttl", format="turtle")
nonsimple = {p for p in tbox.subjects(RDF.type, OWL.TransitiveProperty)}
nonsimple |= {p for p in tbox.subjects(OWL.propertyChainAxiom, None)}
grew = True
while grew:                      # propagates upwards through subPropertyOf
    grew = False
    for sub, sup in tbox.subject_objects(RDFS.subPropertyOf):
        if sub in nonsimple and sup not in nonsimple:
            nonsimple.add(sup); grew = True
forbidden = {OWL.FunctionalProperty, OWL.InverseFunctionalProperty,
             OWL.IrreflexiveProperty, OWL.AsymmetricProperty}
bad = [(str(p).split("#")[-1], str(c).split("#")[-1])
       for c in forbidden for p in tbox.subjects(RDF.type, c) if p in nonsimple]
bad += [(str(p).split("#")[-1], "propertyDisjointWith")
        for p, q in tbox.subject_objects(OWL.propertyDisjointWith)
        if p in nonsimple or q in nonsimple]
card = [OWL.cardinality, OWL.maxCardinality, OWL.minCardinality,
        OWL.qualifiedCardinality, OWL.maxQualifiedCardinality, OWL.minQualifiedCardinality]
bad += [(str(tbox.value(r, OWL.onProperty)).split("#")[-1], "cardinality")
        for k in card for r in tbox.subjects(k, None)
        if tbox.value(r, OWL.onProperty) in nonsimple]
check("OWL 2 DL: no non-simple property is declared functional, irreflexive, "
      "asymmetric, disjoint or cardinality-restricted", not bad, str(bad))
check("OWL 2 DL: isJuralOppositeOf is simple, as its irreflexivity requires",
      N.isJuralOppositeOf not in nonsimple)
check("OWL 2 DL: the two conflict relations are simple",
      N.deonticallyContradicts not in nonsimple
      and N.deonticallyConflictsWith not in nonsimple)
check("isJuralOppositeOf is NOT transitive (the opposite of the opposite is itself)",
      (N.isJuralOppositeOf, RDF.type, OWL.TransitiveProperty) not in tbox)
check("isJuralOppositeOf is NOT functional (several norms may confer the opposite)",
      (N.isJuralOppositeOf, RDF.type, OWL.FunctionalProperty) not in tbox)

# ── 2e. cycles, Strict and chained repeal (separate fixture) ─────────
CYC = ONTO / "deriv" / "tests" / "test-cycles.ttl"
TC = Namespace("https://example.org/norma-cycles#")
subprocess.run([sys.executable, str(ONTO / "deriv" / "derive.py"), str(CYC),
                "-o", f"{tmp}/cyc.ttl"], check=True, capture_output=True)
g_cyc = Graph().parse(f"{tmp}/cyc.ttl", format="turtle")

def cyc_of(*locals_):
    want = {TC[x] for x in locals_}
    for c in g_cyc.subjects(RDF.type, ND.PrevalenceCycle):
        if set(g_cyc.objects(c, ND.involvesNorm)) == want:
            return c
    return None
def kind_of(c):
    k = g_cyc.value(c, ND.hasCycleKind)
    return str(k).split("#")[-1] if k else None

stat_c = next(o for o in g_cyc.subjects(RDF.type, ND.PrevalenceOrdering)
              if not list(g_cyc.objects(o, ND.forFactPattern)))
EC = {}
for ev in g_cyc.subjects(ND.inOrdering, stat_c):
    EC[str(g_cyc.value(ev, ND.evaluatedNorm)).split("#")[-1]] = \
        g_cyc.value(ev, ND.prevalenceLevel)
C0 = {}
o0 = next(o for o in g_cyc.subjects(RDF.type, ND.PrevalenceOrdering)
          if list(g_cyc.objects(o, ND.forFactPattern)))
for ev in g_cyc.subjects(ND.inOrdering, o0):
    C0[str(g_cyc.value(ev, ND.evaluatedNorm)).split("#")[-1]] = \
        str(g_cyc.value(ev, ND.hasApplicabilityStatus)).split("#")[-1]

check("K1: Kahn detects the cycle and the ladder is marked NOT acyclic",
      g_cyc.value(stat_c, ND.isAcyclic).toPython() is False)
check("K2: a 2-cycle with DIFFERENT principles is a second-degree conflict "
      "(Bobbio), not an annotation error",
      kind_of(cyc_of("n_s1", "n_s2")) == "SecondDegreeConflict")
check("K3: and BOTH competing principles are reported, without choosing",
      {str(p).split("#")[-1] for p in
       g_cyc.objects(cyc_of("n_s1", "n_s2"), ND.citesCompetingPrinciple)}
      == {"LexSpecialis", "LexPosterior"})
check("K4: the SAME principle in both directions IS an annotation contradiction",
      kind_of(cyc_of("n_t1", "n_t2")) == "AnnotationContradiction")
check("K5: a loop of exceptions with no principle is an irresoluble antinomy",
      kind_of(cyc_of("n_u1", "n_u2")) == "IrresolubleAntinomy")
check("K6: in these cycles, with no attack from outside, the norms are UNDECIDED",
      all(C0[n] == "Undecided" for n in
          ("n_s1", "n_s2", "n_t1", "n_t2", "n_u1", "n_u2")))
check("K7: the norms of one cycle SHARE a rung, because the level is "
      "computed on the condensation into strongly connected components",
      EC["n_s1"] is not None and EC["n_s1"] == EC["n_s2"]
      and EC["n_u1"] is not None and EC["n_u1"] == EC["n_u2"])
check("K8: a Strict norm resists defeat and stays in force",
      C0["n_v"] == "Applicable")
check("K9: the void edge against a Strict norm is excluded from the digraph, "
      "so its level does not claim that anything prevails over it",
      int(EC["n_v"]) == 0)
check("K10: NO REVIVAL — w1 repeals w2, which had repealed w3: both stay out",
      "n_w2" not in EC and "n_w3" not in EC)
check("K11: the repealing norm in force stays in the system", int(EC["n_w1"]) == 0)
check("K12: cycles hang from the ordering that found them",
      set(g_cyc.objects(stat_c, ND.inCycle)) and
      all((stat_c, ND.inCycle, c) in g_cyc or (o0, ND.inCycle, c) in g_cyc
          for c in g_cyc.subjects(RDF.type, ND.PrevalenceCycle)))

# ── 2f. the two algorithms, cross-checked ────────────────────────────
# Kahn says WHETHER there is a cycle (its remainder is non-empty) and gives the
# canonical layers; Kosaraju says WHICH norms form it. They are independent
# implementations and must agree, so they are cross-checked on hand-built graphs.
sys.path.insert(0, str(ONTO / "deriv"))
from prevalence import cycles as _cyc, grounded as _gr, kahn as _kahn, strata as _st

CASES = {
    "chain":         ("abc",  {("a","b"),("b","c")}),
    "diamond":       ("abcd", {("a","b"),("a","c"),("b","d"),("c","d")}),
    "2-cycle":       ("pq",   {("p","q"),("q","p")}),
    "3-cycle":       ("xyz",  {("x","y"),("y","z"),("z","x")}),
    "self-loop":     ("a",    {("a","a")}),
    "cycle+downstream":("xycb", {("x","y"),("y","x"),("c","x"),("c","y"),("x","b")}),
    "no edges":      ("mn",   set()),
}
bad = []
for name, (nodes, edges) in CASES.items():
    order, levels, rest = _kahn(nodes, edges)
    comps = _cyc(nodes, edges)
    if bool(rest) != bool(comps):
        bad.append(f"{name}: remainder={rest} components={comps}")
    if set(levels) != set(order):
        bad.append(f"{name}: level defined outside the topological order")
    if any(set(comp) - set(rest) for comp in comps):
        bad.append(f"{name}: component outside Kahn's remainder")
check("A1: Kahn and Kosaraju agree — there is a remainder if and only if there "
      "is a strongly connected component, and every component lies in the remainder", not bad, "; ".join(bad))
check("A2: kahn() defines a level exactly for the nodes it manages to order",
      not [c for c in bad if "level" in c])
check("A15: strata() gives a level to ALL nodes, including those on a cycle and "
      "their acyclic descendants, which Kahn left without a rung",
      _st("abc", {("a","b"),("b","a"),("b","c")})[0] == {"a": 0, "b": 0, "c": 1})
check("A16: on an acyclic digraph the condensation matches Kahn, "
      "so the change does not alter the ordinary case",
      _st(*CASES["diamond"])[0] == _kahn(*CASES["diamond"])[1])
check("A17: downstream of a cycle attacked from outside the three rungs "
      "are ordered: attacker 0, cycle 1, descendant 2",
      _st(*CASES["cycle+downstream"])[0] == {"c": 0, "x": 1, "y": 1, "b": 2})
check("A18: strata() reports the same non-trivial components as cycles()",
      _st(*CASES["3-cycle"])[1] == _cyc(*CASES["3-cycle"]))
order, levels, _ = _kahn(*CASES["diamond"])
check("A11: being on a CYCLE does not imply undecided — with a<->b and an "
      "undefeated c defeating a, grounded semantics gives c applicable, "
      "a defeated and b APPLICABLE, because b is reinstated",
      _gr("abc", {("a","b"),("b","a"),("c","a")})
      == {"a": "Defeated", "b": "Applicable", "c": "Applicable"})
check("A12: and the cycle is still REPORTED, even though its norms are decided",
      _cyc("abc", {("a","b"),("b","a"),("c","a")}) == [["a","b"]])
check("A13: conversely, a norm OUTSIDE every cycle attacked only from an "
      "undecided one is itself undecided",
      _gr("pqd", {("p","q"),("q","p"),("p","d")})["d"] == "Undecided")
check("A14: so Undecided follows the fixpoint, not membership of a cycle",
      "a" in [n for n in _cyc("abc", {("a","b"),("b","a"),("c","a")})[0]]
      and _gr("abc", {("a","b"),("b","a"),("c","a")})["a"] != "Undecided")
check("A3: layers by LONGEST path, not by the first path found "
      "(in the diamond d is at 2, not 1)", levels["d"] == 2)
check("A4: every edge goes from a strictly lower level to a higher one",
      all(levels[a] < levels[b] for a, b in CASES["diamond"][1]))
check("A5: the topological order respects every edge",
      all(order.index(a) < order.index(b) for a, b in CASES["diamond"][1]))
check("A6: Kahn is deterministic: two runs give the same order",
      _kahn(*CASES["diamond"])[0] == _kahn(*CASES["diamond"])[0])
check("A7: reinstatement along the chain — c is back in force",
      _gr(*CASES["chain"])["c"] == "Applicable")
check("A8: a 3-cycle leaves all three undecided",
      set(_gr(*CASES["3-cycle"]).values()) == {"Undecided"})
check("A9: downstream of a cycle withdrawn from outside, b stays IN FORCE "
      "(which a single topological pass gets wrong)",
      _gr(*CASES["cycle+downstream"])["b"] == "Applicable")
check("A10: with no edges, everything in force and at level 0",
      set(_gr(*CASES["no edges"]).values()) == {"Applicable"}
      and set(_kahn(*CASES["no edges"])[1].values()) == {0})

# ── 2g. roles, parties and role assignment (Article 25 experiment) ───
# The fixture is the real experiment on Regulation (EU) 2024/1689, not made-up
# data: it measures whether the Art. 16 obligation, addressed to the PROVIDER,
# reaches a party that counts as provider under Art. 25(1)(b).
ART25 = ONTO / "deriv" / "tests" / "test-roles-art25.ttl"
AA = Namespace("https://w3id.org/norma-abox/art25#")
subprocess.run([sys.executable, str(ONTO / "deriv" / "derive.py"), str(ART25),
                "-o", f"{tmp}/a25.ttl"], check=True, capture_output=True)
g25 = Graph().parse(f"{tmp}/a25.ttl", format="turtle")
a25 = Graph().parse(ART25, format="turtle")

def reach(case):
    """Norms that reach Acme in that case."""
    o = next(x for x in g25.subjects(RDF.type, ND.PrevalenceOrdering)
             if g25.value(x, ND.forFactPattern) == AA[case])
    out = set()
    for ev in g25.subjects(ND.inOrdering, o):
        if AA.Party_Acme in set(g25.objects(ev, ND.reachesParty)):
            out.add(str(g25.value(ev, ND.evaluatedNorm)).split("#")[-1])
    return out
def st25(case, norm):
    o = next(x for x in g25.subjects(RDF.type, ND.PrevalenceOrdering)
             if g25.value(x, ND.forFactPattern) == AA[case])
    for ev in g25.subjects(ND.inOrdering, o):
        if g25.value(ev, ND.evaluatedNorm) == AA[norm]:
            return str(g25.value(ev, ND.hasApplicabilityStatus)).split("#")[-1]

check("R1: a norm addressed to a ROLE reaches the PARTY the case places "
      "in that role (Art. 26 to the deployer)",
      "OBL_Art26_deployer" in reach("Case_acme_unmodified"))
check("R2: RECLASSIFICATION under Art. 25(1)(b) — after the substantial modification "
      "Acme counts as provider, and Art. 16 reaches it",
      "OBL_Art16_provider" in reach("Case_acme_modified"))
check("R3: and it is RELATIVE TO THE CASE: without modification, Art. 16 does NOT reach it",
      "OBL_Art16_provider" not in reach("Case_acme_unmodified"))
check("R4: because the constitutive rule is not activated in that case",
      st25("Case_acme_unmodified", "FCT_Art25_1_counts_as_provider") == "NotActivated"
      and st25("Case_acme_modified", "FCT_Art25_1_counts_as_provider") == "Applicable")
check("R5: the reclassified capacity cites its legal basis; the original one, "
      "given by the facts, needs none",
      a25.value(AA.RA_acme_provider, N.assignedUnderRule) == AA.FCT_Art25_1_counts_as_provider
      and a25.value(AA.RA_acme_deployer, N.assignedUnderRule) is None)
check("R6: the constitutive rule states WHICH role it confers, which is what gives "
      "it formal consequence",
      a25.value(AA.FCT_Art25_1_counts_as_provider, N.confersRole) == AA.Role_Provider)
check("R7: reach is NOT materialised on the norm or the party, but on the "
      "evaluation, which is the only thing relative to the case",
      not list(g25.objects(AA.OBL_Art16_provider, ND.reachesParty))
      and not list(g25.subject_objects(N.hasAssignedRole)) )

# ── 2h. constitutive -> regulative chaining (Art. 6 of the AI Act) ──
# The fixture reproduces the REAL structure: Art. 6(3) defeats the
# CLASSIFICATION of Art. 6(2), not the obligations, and Articles 16 and 26 hang
# from it. With the shortcut wiring the exception straight to Art. 16, Art. 26
# stays undefeated and the legal result is false. These checks exist to prevent
# that regression.
CA = ONTO / "deriv" / "tests" / "test-counts-as.ttl"
TC2 = Namespace("https://example.org/norma-countsas#")
subprocess.run([sys.executable, str(ONTO / "deriv" / "derive.py"), str(CA),
                "-o", f"{tmp}/ca.ttl"], check=True, capture_output=True)
g_ca = Graph().parse(f"{tmp}/ca.ttl", format="turtle")
a_ca = Graph().parse(CA, format="turtle")

def ca_st(case):
    o = next(x for x in g_ca.subjects(RDF.type, ND.PrevalenceOrdering)
             if g_ca.value(x, ND.forFactPattern) == TC2[case])
    out = {}
    for ev in g_ca.subjects(ND.inOrdering, o):
        out[str(g_ca.value(ev, ND.evaluatedNorm)).split("#")[-1]] = \
            str(g_ca.value(ev, ND.hasApplicabilityStatus)).split("#")[-1]
    return out

CAN, CNA, CPR = ca_st("C_annex"), ca_st("C_narrow"), ca_st("C_prof")

check("CA1: the constitutive rule of 6(2) ESTABLISHES the fact, and with Annex "
      "III alone both obligations are applicable",
      CAN["fct_62"] == "Applicable"
      and CAN["obl_16"] == "Applicable" and CAN["obl_26"] == "Applicable")
check("CA2: defeating the CLASSIFICATION withdraws BOTH obligations. This is the "
      "bug the shortcut produced: Art. 26 came out applicable without high risk",
      CNA["fct_62"] == "Defeated"
      and CNA["obl_16"] == "NotActivated" and CNA["obl_26"] == "NotActivated")
check("CA3: and reinstatement propagates THROUGH the classification: the final "
      "subparagraph of 6(3) defeats the exception and both come back",
      CPR["fct_63"] == "Defeated" and CPR["fct_62"] == "Applicable"
      and CPR["obl_16"] == "Applicable" and CPR["obl_26"] == "Applicable")
check("CA4: the institutional fact is NOT annotated in any case: it is derived",
      not [c for c in a_ca.subjects(RDF.type, N.FactPattern)
           for t in a_ca.objects(c, N.holdsTrigger)
           if t in {TC2.te_hr_16, TC2.te_hr_26}])
check("CA5: no defeater targets the obligations; the defeat falls "
      "on the constitutive rule",
      not [d for d in a_ca.subjects(N.defeatedNorm, None)
           if a_ca.value(d, N.defeatedNorm) in {TC2.obl_16, TC2.obl_26}])
check("CA6: the chaining is carried by norma:establishesTrigger, and covers "
      "both obligations",
      set(a_ca.objects(TC2.fct_62, N.establishesTrigger))
      == {TC2.te_hr_16, TC2.te_hr_26})
# A role assignment is asserted and never retracted, so it may end up citing a
# rule that does not apply in that case. Nothing is derived: a warning is issued.
UR = ONTO / "deriv" / "tests" / "test-unsound-role.ttl"
_ur = subprocess.run([sys.executable, str(ONTO / "deriv" / "derive.py"), str(UR),
                      "-o", f"{tmp}/ur.ttl"], capture_output=True, text=True)
check("CA8: a warning is issued for a role assignment whose justifying rule does not apply in the case",
      "role assignment RA cites fct25" in _ur.stdout and "NotActivated" in _ur.stdout,
      _ur.stdout[-300:])

# C10: dispatch by content, not by extension
import tempfile as _tf
from rdflib import Graph as _G
_rdfx = f"{tmp}/abox.rdf"
_G().parse(ONTO / "deriv" / "tests" / "test-counts-as.ttl", format="turtle").serialize(_rdfx, format="xml")
_a = subprocess.run([sys.executable, str(ONTO / "deriv" / "derive.py"), _rdfx,
                     "-o", f"{tmp}/x1.ttl"], capture_output=True, text=True, check=True)
_b = subprocess.run([sys.executable, str(ONTO / "deriv" / "derive.py"),
                     str(ONTO / "deriv" / "tests" / "test-counts-as.ttl"),
                     "-o", f"{tmp}/x2.ttl"], capture_output=True, text=True, check=True)
check("C10: an ABox in RDF/XML gives the SAME derived graph as in Turtle; the "
      "format is decided by content, not by extension",
      len(_G().parse(f"{tmp}/x1.ttl", format="turtle"))
      == len(_G().parse(f"{tmp}/x2.ttl", format="turtle")))

# The permissive reading of the counterparty is non-monotonic, so when it is
# in play it must be declared. Both ways: the main fixture has norms without a
# counterparty and declares it; the Art. 6 fixture names them all and does not.
check("CP1: normad:OpenCounterparty is declared when some norm with an action "
      "lacks a counterparty, because 04c and 05a-c apply the permissive reading",
      (None, ND.computedUnderAssumption, ND.OpenCounterparty) in g_open)
check("CP2: and it is NOT declared when every norm with an action names one, "
      "because then the strict reading comes for free",
      (None, ND.computedUnderAssumption, ND.OpenCounterparty) not in g_ca)
# n_b_B is exactly the norm the old count missed: a PERMISSION with an action
# and no counterparty. It enters 05a and 04c, so it depends on the assumption,
# and yet it entails no obligation.
_abox = Graph().parse(ABOX, format="turtle")
# The minimal case: P(x) and F(x) for the same role, neither with a
# counterparty. It yields 1 contradiction and 1 opposition, both resting on the
# permissive reading, so the activity MUST declare it and the warning must name
# both norms.
SC = ONTO / "deriv" / "tests" / "test-silent-counterparty.ttl"
_sc = subprocess.run([sys.executable, str(ONTO / "deriv" / "derive.py"), str(SC),
                      "-o", f"{tmp}/sc.ttl"], capture_output=True, text=True, check=True)
g_sc = Graph().parse(f"{tmp}/sc.ttl", format="turtle")
check("CP4: with P(x) and F(x) and no counterparty, contradiction and opposition "
      "come out, and the activity declares normad:OpenCounterparty",
      len(list(g_sc.subject_objects(N.deonticallyContradicts))) == 2
      and len(list(g_sc.subject_objects(N.isJuralOppositeOf))) == 2
      and (None, ND.computedUnderAssumption, ND.OpenCounterparty) in g_sc)
check("CP5: the warning names BOTH norms, the permission too, because a "
      "privilege without a counterparty loses its no-right just as a duty "
      "loses its claim",
      "'F1', 'P1'" in _sc.stdout or "'P1', 'F1'" in _sc.stdout, _sc.stdout[-200:])

check("CP3: the assumption covers PERMISSIONS without a counterparty, which "
      "entail no obligation and which a count over entailsObligatory missed",
      (T["n_b_B"], RDF.type, N.Permission) in _abox
      and list(_abox.objects(T["n_b_B"], N.hasLegalAction))
      and not list(_abox.objects(T["n_b_B"], N.hasCounterparty))
      and not list(g_open.objects(T["n_b_B"], N.entailsObligatory)))

check("CA7: the activity declares the chaining assumption",
      (None, ND.computedUnderAssumption, ND.InstitutionalFactsChained) in g_ca)

# ── 2i. both serialisations of each ontology, isomorphic ─────────────
# They are published together: whoever reads the RDF/XML must get exactly the
# same ontology as whoever reads the Turtle, blank nodes included.
from rdflib.compare import isomorphic as _isomorphic
_diverging = [stem for stem in ("norma-ontology-v2", "norma-o-deriv")
              if not _isomorphic(Graph().parse(ONTO / f"{stem}.ttl", format="turtle"),
                                 Graph().parse(ONTO / f"{stem}.rdf", format="xml"))]
check("RDF1: Turtle and RDF/XML are isomorphic for the core and the module",
      not _diverging, f"diverging: {_diverging}")

# ── 3. negations ─────────────────────────────────────────────────────
work = Graph().parse(ONTO/"norma-ontology-v2.ttl", format="turtle")
work.parse(ABOX, format="turtle"); work += g_open
pairs = set(work.subject_objects(N.isNegationOf))
check("isNegationOf in both directions", all((b,a) in pairs for a,b in pairs))
multi = [a for a in {a for a,_ in pairs} if len({b for x,b in pairs if x==a}) > 1]
check("no action with two negations", not multi, str(multi))

# ── 4. byte-for-byte idempotence ─────────────────────────────────────
run(f"{tmp}/again.ttl")
check("idempotent: two runs, same graph",
      Path(f"{tmp}/open.nt").read_text() == Path(f"{tmp}/again.nt").read_text())

# ── 5. consistency and integrity check ───────────────────────────────
from owlready2 import World, sync_reasoner, OwlReadyInconsistentOntologyError
def consistent_file(abox, derived):
    g = Graph().parse(ONTO/"norma-ontology-v2.ttl", format="turtle")
    g.parse(ONTO/"norma-o-deriv.ttl", format="turtle")
    g.parse(abox, format="turtle"); g.parse(derived, format="turtle")
    for t in list(g.triples((None, OWL.imports, None))): g.remove(t)
    fd, p = tempfile.mkstemp(suffix=".owl", dir=tmp); os.close(fd); g.serialize(p, format="xml")
    w = World(); w.get_ontology("file://" + p).load()
    try:
        sync_reasoner(w, debug=0, ignore_unsupported_datatypes=True); return True
    except OwlReadyInconsistentOntologyError: return False

def consistent(extra_ttl=""):
    g = Graph().parse(ONTO/"norma-ontology-v2.ttl", format="turtle")
    g.parse(ONTO/"norma-o-deriv.ttl", format="turtle")
    g.parse(ABOX, format="turtle"); g += g_open
    if extra_ttl:
        g.parse(data=f"@prefix norma: <{N}> .\n@prefix : <{T}> .\n@prefix owl: <{OWL}> .\n" + extra_ttl, format="turtle")
    for t in list(g.triples((None, OWL.imports, None))): g.remove(t)
    fd, p = tempfile.mkstemp(suffix=".owl", dir=tmp); os.close(fd); g.serialize(p, format="xml")
    w = World(); w.get_ontology("file://" + p).load()
    try:
        sync_reasoner(w, debug=0, ignore_unsupported_datatypes=True); return True
    except OwlReadyInconsistentOntologyError: return False
check("TBox + module + ABox + derived: consistent", consistent())
check("R8: LegalRole and LegalParty are disjoint: a party is not a role",
      not consistent(":Party_X a owl:NamedIndividual, norma:LegalRole, norma:LegalParty ."))
check("R9: the Art. 25 experiment ABox plus its derived graph are consistent "
      "with the TBox",
      consistent_file(ART25,
                      f"{tmp}/a25.ttl"))
def derives(s, p, o):
    g = Graph().parse(ONTO/"norma-ontology-v2.ttl", format="turtle")
    g.parse(ABOX, format="turtle"); g += g_open
    for t in list(g.triples((None, OWL.imports, None))): g.remove(t)
    fd, pth = tempfile.mkstemp(suffix=".owl", dir=tmp); os.close(fd); g.serialize(pth, format="xml")
    w = World(); w.get_ontology("file://" + pth).load()
    sync_reasoner(w, infer_property_values=True, debug=0, ignore_unsupported_datatypes=True)
    return (s, N[p], o) in w.as_rdflib_graph()
dn = positions(g_open, "Duty", "n_obl")[0]; cn = positions(g_open, "Claim", "n_obl")[0]
check("H10: HermiT INFERS the counterparty of the duty (not annotated)", derives(dn, "hasPositionCounterparty", T["B"]))
check("H11: HermiT PROPAGATES the content to the correlative", derives(cn, "concernsLegalAction", T["act_o"]))
check("integrity: injecting P(x) and ¬P(x) makes it inconsistent",
      not consistent(":n_bad a owl:NamedIndividual, norma:Obligation ; "
                     "norma:entailsPermitted :act_o ; norma:entailsNotPermitted :act_o ."))

print(f"\nfailures: {len(fails)}" + (f"  {fails}" if fails else ""))
sys.exit(1 if fails else 0)
