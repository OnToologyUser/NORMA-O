"""NORMA-O 2.0 engine: one hand-written annotation in, everything that follows from it out.

Part of the NORMA-O release, https://github.com/sheyls/NORMA-O (CC BY 4.0).

    python engine.py path/to/annotation.ttl                 # check, derive, bundle, report
    python engine.py path/to/annotation.ttl --reason        # ...and check OWL consistency with HermiT
    python engine.py check path/to/annotation.ttl           # only check the annotation

You write ONE Turtle file: the norms, the cases, and whatever else you annotate
(sources, provenance), in NORMA-O 2.0. Alternative readings, if any, go next to
it as `variant-*.ttl`, each named by a first line `# Reading: <name>`, or are
passed with --variant NAME=FILE. The engine then, for each reading:

  check    reports what the derivation needs and is missing: an addressee and an
           action on every regulative norm (errors), a counterparty, a source,
           provenance, a review status, a binding force, cases (warnings)
  derive   runs deriv/derive.py: deontic closure, Hohfeldian positions, deontic
           relations, the prevalence ladder (topological order, cycles) and, per
           case, institutional facts chained to a fixpoint, the applicability and
           reach of every norm, and weak permissions
  bundle   writes ONE self-contained file per reading: the annotation plus its
           derivation, importing this folder's ontology files
  reason   (with --reason; needs owlready2 and Java) loads ontology + bundle in
           HermiT and reports whether they are consistent
  report   a review sheet (one row per norm) and the status of every norm in
           every case under every reading, with what each reading changes

Everything is written to <annotation folder>/build/. The annotation file is
never modified: as `normad:DerivationActivity` requires, a derived graph is
regenerated, never merged back into the annotation it was derived from.
Requires rdflib (deriv/requirements.txt).
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS

HERE = Path(__file__).resolve().parent            # the release folder: ontology, module, deriv/
PY = sys.executable
N = Namespace("https://w3id.org/def/norma-o#")
ND = Namespace("https://w3id.org/def/norma-o/deriv#")
GAP = Namespace("https://example.org/norma-gap#")   # optional project vocabulary for gaps, if present
REG = ("Obligation", "Prohibition", "Permission", "Facultative", "Recommendation", "NegativeRecommendation")


def say(step: str, msg: str) -> None:
    print(f"[{step:7}] {msg}")


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(Path.cwd()))
    except ValueError:
        return str(p)


class Job:
    def __init__(self, annotation: Path, variants: list[str] | None = None, out: Path | None = None):
        self.ann = annotation.resolve()
        if not self.ann.is_file():
            sys.exit(f"annotation not found: {annotation}")
        self.out = (out or self.ann.parent / "build").resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.variants: dict[str, Path] = {}
        found = variants or [str(p) for p in sorted(self.ann.parent.glob("variant-*.ttl"))]
        for v in found:
            name, _, path = v.rpartition("=") if "=" in v else ("", "", v)
            p = Path(path).resolve()
            first = p.read_text(encoding="utf-8").splitlines()[0] if p.exists() else ""
            self.variants[name or (first[len("# Reading:"):].strip() if first.startswith("# Reading:") else p.stem)] = p

    def stem(self, variant: Path | None = None) -> str:
        return self.ann.stem + (f"+{variant.stem}" if variant else "")

    def derived(self, variant=None): return self.out / f"{self.stem(variant)}.derived.ttl"
    def bundle(self, variant=None): return self.out / f"{self.stem(variant)}.bundle.ttl"
    def readings(self): return [(None, None)] + list(self.variants.items())


# ── check ────────────────────────────────────────────────────────────────────
def check(job: Job) -> bool:
    g = Graph().parse(job.ann)
    norms = {s for k in REG + ("ConstitutiveRule",) for s in g.subjects(RDF.type, N[k])}
    reg = {s for k in REG for s in g.subjects(RDF.type, N[k])}
    cases = set(g.subjects(RDF.type, N.FactPattern))
    gaps = set(g.subjects(RDF.type, GAP.Gap))
    say("check", f"{rel(job.ann)}: {len(g)} triples, {len(norms)} norms ({len(reg)} regulative, "
                 f"{len(norms) - len(reg)} constitutive), {len(set(g.subjects(RDF.type, N.LegalCondition)))} conditions, "
                 f"{len(cases)} cases" + (f", {len(gaps)} gaps" if gaps else ""))
    for name, p in job.variants.items():
        say("check", f"reading «{name}»: {rel(p)} ({len(Graph().parse(p))} triples)")
    short = lambda u: str(u).rsplit("#", 1)[-1]
    errors = {"regulative norm without norma:hasLegalAgent (no position, no reach)":
                  [n for n in reg if (n, N.hasLegalAgent, None) not in g],
              "regulative norm without norma:hasLegalAction (outside the closure)":
                  [n for n in reg if (n, N.hasLegalAction, None) not in g]}
    warnings = {"regulative norm without norma:hasCounterparty (no correlative claim/no-right)":
                    [n for n in reg if (n, N.hasCounterparty, None) not in g],
                "norm without norma:hasLegalSource": [n for n in norms if (n, N.hasLegalSource, None) not in g],
                "norm without provenance (wasAttributedToAnnotator / hasExtractionMethod)":
                    [n for n in norms if (n, N.wasAttributedToAnnotator, None) not in g or (n, N.hasExtractionMethod, None) not in g],
                "norm without norma:hasReviewStatus": [n for n in norms if (n, N.hasReviewStatus, None) not in g],
                "regulative norm without norma:hasBindingForce": [n for n in reg if (n, N.hasBindingForce, None) not in g]}
    partial = {(short(c), short(cond)) for c, t1 in g.subject_objects(N.holdsTrigger) for cond in g.subjects(N.hasTrigger, t1)
               for t2 in g.objects(cond, N.hasTrigger)
               if g.value(t1, N.hasOutcome) == g.value(t2, N.hasOutcome) and (c, N.holdsTrigger, t2) not in g}
    if partial:
        warnings["case holding only some triggers of a condition"] = sorted(partial)
    if not cases:
        warnings["no norma:FactPattern: nothing is evaluated per case"] = ["(annotation)"]
    ok = True
    for kind, items in (("ERROR", errors), ("warn", warnings)):
        for what, xs in items.items():
            if xs:
                ok &= kind != "ERROR"
                say("check", f"{kind}: {len(xs)} {what}: "
                    + ", ".join(short(x) if not isinstance(x, tuple) else "/".join(x) for x in sorted(xs, key=str))[:400])
    if ok and not any(warnings.values()):
        say("check", "the annotation has everything the derivation uses")
    return ok


# ── derive ───────────────────────────────────────────────────────────────────
def derive(job: Job) -> None:
    for name, var in job.readings():
        abox = job.ann
        if var is not None:                           # a reading = the annotation + its variant, in one input
            abox = job.out / f"{job.stem(var)}.abox.ttl"
            abox.write_text(job.ann.read_text(encoding="utf-8") + "\n" + var.read_text(encoding="utf-8"), encoding="utf-8")
        out = job.derived(var)
        r = subprocess.run([PY, str(HERE / "deriv" / "derive.py"), str(abox), "-o", str(out)], cwd=HERE,
                           capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"derive.py failed for «{name or 'base'}»:\n{r.stderr}")
        warn = [l[4:] for l in r.stdout.splitlines() if l.startswith("[!]")]
        say("derive", f"{name or 'base reading'}: {rel(out)} ({len(Graph().parse(out))} triples)"
                      + ("; derive.py warns: " + " | ".join(warn) if warn else ""))


# ── bundle ───────────────────────────────────────────────────────────────────
def bundle(job: Job) -> None:
    for name, var in job.readings():
        g = Graph().parse(job.ann)
        if var is not None:
            g.parse(var)
        g.parse(job.derived(var))
        onto = next(g.subjects(RDF.type, OWL.Ontology), None)
        header = [(p, o) for p, o in g.predicate_objects(onto) if p != OWL.imports] if onto is not None else []
        for o in list(g.subjects(RDF.type, OWL.Ontology)):
            g.remove((o, None, None))
        iri = URIRef((str(onto) if onto is not None else "https://example.org/" + job.ann.stem) + "/" + job.stem(var))
        g.add((iri, RDF.type, OWL.Ontology))
        for p, o in header:                         # label, licence, seeAlso… carried over; imports made local
            g.add((iri, p, o))
        for f in ("norma-ontology-v2.ttl", "norma-o-deriv.ttl"):
            g.add((iri, OWL.imports, URIRef((HERE / f).as_uri())))
        g.serialize(job.bundle(var), format="turtle")
        say("bundle", f"{name or 'base reading'}: {rel(job.bundle(var))} ({len(g)} triples)")


# ── reason ───────────────────────────────────────────────────────────────────
def reason(job: Job) -> bool:
    """Ontology + derivation module + bundle in HermiT, as deriv/tests/check_deriv.py does."""
    try:
        from owlready2 import OwlReadyInconsistentOntologyError, World, sync_reasoner
    except ImportError:
        say("reason", "skipped: needs owlready2 (pip install owlready2) and Java"); return True
    ok = True
    for name, var in job.readings():
        g = Graph().parse(HERE / "norma-ontology-v2.ttl", format="turtle")
        g.parse(HERE / "norma-o-deriv.ttl", format="turtle")
        g.parse(job.bundle(var))
        for t in list(g.triples((None, OWL.imports, None))):
            g.remove(t)
        fd, p = tempfile.mkstemp(suffix=".owl"); os.close(fd)
        g.serialize(p, format="xml")
        w = World(); w.get_ontology("file://" + p).load()
        try:
            sync_reasoner(w, debug=0, ignore_unsupported_datatypes=True)
            say("reason", f"{name or 'base reading'}: consistent (HermiT, ontology + module + bundle)")
        except OwlReadyInconsistentOntologyError:
            ok = False
            say("reason", f"{name or 'base reading'}: INCONSISTENT (HermiT)")
        finally:
            os.unlink(p)
    return ok


# ── report ───────────────────────────────────────────────────────────────────
def report(job: Job) -> None:
    g = Graph().parse(job.ann)
    ln = lambda u: str(u).rsplit("#", 1)[-1]
    lab = lambda u: str(g.value(u, RDFS.label) or ln(u))
    j = lambda xs: ", ".join(sorted(set(xs)))
    order = re.findall(r'norma:deonticId "([^"]+)"', job.ann.read_text(encoding="utf-8"))
    byid = {str(g.value(n, N.deonticId)): n for n in g.subjects(N.deonticId, None)}
    cond_of = {t: c for c, t in g.subject_objects(N.hasTrigger)}
    estab_by, defeats, defeated_by = {}, {}, {}
    for r, t in g.subject_objects(N.establishesTrigger):
        estab_by.setdefault(t, set()).add(r)
    for a, b in g.subject_objects(N.isExceptionTo):
        defeats.setdefault(a, set()).add(b); defeated_by.setdefault(b, set()).add(a)
    for d in set(g.subjects(RDF.type, N.ExceptionDefeater)) | set(g.subjects(RDF.type, N.ConflictDefeater)):
        a, b = g.value(d, N.defeatingNorm), g.value(d, N.defeatedNorm)
        defeats.setdefault(a, set()).add(b); defeated_by.setdefault(b, set()).add(a)
    cols = ["id", "section", "type", "statement", "bearer", "counterparty", "action", "deadline", "activated_when (any of)",
            "activated_by_rule", "establishes_for", "confers_role", "defeats", "defeated_by", "review_status", "gaps",
            "expert_verdict", "expert_comment"]
    rows = []
    for nid in sorted(byid, key=lambda i: order.index(i) if i in order else len(order)):
        n = byid[nid]
        trig = list(g.subjects(N.activatesNorm, n))
        conds = sorted({str(g.value(cond_of[t], N.conditionStatement)) for t in trig if t in cond_of})
        rows.append({"id": nid, "section": str(g.value(n, N.fromArticle) or ""),
                     "type": next((ln(t) for t in g.objects(n, RDF.type) if ln(t) in REG + ("ConstitutiveRule",)), ""),
                     "statement": str(g.value(n, N.normStatement) or g.value(n, N.factStatement) or ""),
                     "bearer": lab(g.value(n, N.hasLegalAgent)) if g.value(n, N.hasLegalAgent) else "",
                     "counterparty": lab(g.value(n, N.hasCounterparty)) if g.value(n, N.hasCounterparty) else "",
                     "action": lab(g.value(n, N.hasLegalAction)) if g.value(n, N.hasLegalAction) else "",
                     "deadline": str(g.value(n, N.deadline) or ""),
                     "activated_when (any of)": " | ".join(conds) if trig else "(unconditional)",
                     "activated_by_rule": j(ln(r) for t in trig for r in estab_by.get(t, ())),
                     "establishes_for": j(ln(m) for t in g.objects(n, N.establishesTrigger) for m in g.objects(t, N.activatesNorm)),
                     "confers_role": j(lab(r) for r in g.objects(n, N.confersRole)),
                     "defeats": j(map(ln, defeats.get(n, ()))), "defeated_by": j(map(ln, defeated_by.get(n, ()))),
                     "review_status": ln(g.value(n, N.hasReviewStatus)) if g.value(n, N.hasReviewStatus) else "",
                     "gaps": "; ".join(sorted({str(g.value(gp, GAP.category)) for gp in g.subjects(GAP.representedAs, n)})),
                     "expert_verdict": "", "expert_comment": ""})
    sheet = job.out / "review-sheet.csv"
    with sheet.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    say("report", f"{rel(sheet)} (review sheet, {len(rows)} norms)")

    per = {}
    for name, var in job.readings():
        d = Graph().parse(job.derived(var))
        st = {}
        for e, o in d.subject_objects(ND.inOrdering):
            c = d.value(o, ND.forFactPattern)
            if c is not None:
                st[(ln(c), ln(d.value(e, ND.evaluatedNorm)))] = ln(d.value(e, ND.hasApplicabilityStatus))
        levels =sorted({int(l) for e, o in d.subject_objects(ND.inOrdering) if d.value(o, ND.forFactPattern) is None
                         for l in d.objects(e, ND.prevalenceLevel)})
        per[name or "base"] = (st, len(levels), next((bool(v) for o in d.subjects(RDF.type, ND.PrevalenceOrdering)
                                                       if d.value(o, ND.forFactPattern) is None for v in d.objects(o, ND.isAcyclic)), True))
    lines = [f"prevalence ladder: " + " | ".join(f"{k}: {n} levels, {'acyclic' if a else 'CYCLES'}" for k, (_, n, a) in per.items()), ""]
    cases = sorted({c for c, _ in per["base"][0]}, key=lambda s: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)])
    lines.append(f"{'case':28} " + "  ".join(f"{'applies':>7} {'defeated':>8} {'not act.':>8}" for _ in per) + "   readings: " + " | ".join(per))
    for c in cases:
        cells = []
        for st, _, _ in per.values():
            k = Counter(v for (cc, _), v in st.items() if cc == c)
            cells.append(f"{k['Applicable']:>7} {k['Defeated']:>8} {k['NotActivated']:>8}")
        lines.append(f"{c:28} " + "  ".join(cells))
    base = per["base"][0]
    for name, (st, _, _) in per.items():
        if name == "base":
            continue
        diff = sorted((c, n, base[(c, n)], v) for (c, n), v in st.items() if (c, n) in base and base[(c, n)] != v)
        added = sorted({n for (c, n) in st if (c, n) not in base})
        lines.append(f"\nwhere «{name}» changes the status of a norm of the base reading: {len(diff)}")
        lines += [f"  {c:24} {n:22} {a} -> {b}" for c, n, a, b in diff]
        if added:
            lines.append(f"norms only in «{name}»: {', '.join(added)}")
    summary = job.out / "summary.txt"
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    say("report", f"{rel(summary)}:\n" + "\n".join("          " + l for l in lines))


def run(job: Job, step: str = "all", with_reason: bool = False) -> bool:
    ok = check(job)
    if step == "check" or not ok:
        return ok
    if step in ("all", "derive"):
        derive(job)
    if step in ("all", "bundle"):
        bundle(job)
    if with_reason or step == "reason":
        ok &= reason(job)
    if step in ("all", "report"):
        report(job)
    return ok


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("args", nargs="+", help="[step] annotation.ttl; step: all (default), check, derive, bundle, reason, report")
    ap.add_argument("--variant", action="append", default=[], metavar="NAME=FILE.ttl",
                    help="alternative reading (default: variant-*.ttl next to the annotation)")
    ap.add_argument("--reason", action="store_true", help="also check OWL consistency with HermiT (owlready2 + Java)")
    ap.add_argument("--out", type=Path, help="output folder (default: <annotation folder>/build)")
    a = ap.parse_args(argv)
    steps = {"all", "check", "derive", "bundle", "reason", "report"}
    step = next((x for x in a.args if x in steps), "all")
    ann = next((Path(x) for x in a.args if x not in steps), None)
    if ann is None:
        ap.error("give the annotation file")
    return 0 if run(Job(ann, a.variant, a.out), step, a.reason) else 1


if __name__ == "__main__":
    sys.exit(main())
