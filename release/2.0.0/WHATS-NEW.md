# NORMA-O 2.0 — What's new

NORMA-O 1.0 let an annotator record **what a provision says**: its deontic
modality, who it addresses, which action and object it regulates, where it comes
from, and who annotated it and how.

NORMA-O 2.0 keeps every term of 1.0 and adds the means to record **how norms
relate to one another and to concrete cases**, and to **compute** what applies,
to whom, and why.

| | |
|---|---|
| Ontology IRI | `https://w3id.org/def/norma-o` |
| Version IRI | `https://w3id.org/def/norma-o/2.0`, with `owl:priorVersion` `https://w3id.org/def/norma-o/1.0` |
| Derivation module | `https://w3id.org/def/norma-o/deriv` (prefix `normad:`), version IRI `…/deriv/1.0` |
| Reference rule set | `deriv/derive.py`, `RULE_SET_VERSION = "norma-derivation/1.0"` |
| Files | `norma-ontology-v2.ttl` / `.rdf`, `norma-o-deriv.ttl` / `.rdf` |

**Contents**

1. [At a glance](#1-at-a-glance)
2. [Compatibility and migration](#2-compatibility-and-migration)
3. [New modelling layers](#3-new-modelling-layers)
4. [The derivation module `normad`](#4-the-derivation-module-normad)
5. [What can now be derived](#5-what-can-now-be-derived)
6. [Worked examples](#6-worked-examples)
7. [Questions 1.0 could not answer](#7-questions-10-could-not-answer)
8. [Tooling](#8-tooling)
9. [Known limitations](#9-known-limitations)
10. [Appendix A — catalogue of new core terms](#appendix-a--catalogue-of-new-core-terms)
11. [Appendix B — catalogue of the `normad` module](#appendix-b--catalogue-of-the-normad-module)

---

## 1. At a glance

### 1.1 Figures

| | v1.0 | v2.0 | `normad` (new) |
|---|---:|---:|---:|
| Classes | 23 | 41 (+18) | 7 |
| Object properties | 41 | 102 (+61) | 11 |
| Datatype properties | 24 | 25 (+1) | 5 |
| Named individuals | 23 | 33 (+10) | 16 |
| SKOS concept schemes | 6 | 9 (+3) | 3 |
| Property chains (`owl:propertyChainAxiom`) | 1 | 4 | – |
| `owl:AllDisjointClasses` axioms | 2 | 4 | – |
| Disjoint / equivalent property pairs | 0 / 0 | 2 / 2 | – |
| Triples | 928 | 1951 | 430 |

All 48 classes of the core and the module are satisfiable under HermiT, and the
whole ontology stays within the OWL 2 DL profile.

### 1.2 The 90 new core terms, by layer

| Layer | Terms | What it adds | Section |
|---|---:|---|---|
| Deontic logic (SDL) | 17 | action negation, the deontic closure, deontic relations between norms, weak permission | [3.1](#31-standard-deontic-logic-actions-their-negation-and-the-closure), [3.2](#32-deontic-relations-between-norms) |
| Hohfeldian positions | 17 | duties, claims, privileges and no-rights, with holder and counterparty | [3.3](#33-hohfeldian-legal-positions) |
| Roles, parties and cases | 16 | the role a law names versus the party that occupies it, and described cases | [3.4](#34-roles-parties-and-cases) |
| Defeasibility | 38 | exceptions, conflicts and repeal; resolution principles; hierarchy of sources; norm strength; the prevalence graph | [3.5](#35-defeasibility-exceptions-conflicts-and-repeal) |
| Counts-as chaining | 2 | constitutive rules that establish institutional facts on which regulative norms depend | [3.6](#36-counts-as-chaining) |

The `normad` module adds 39 terms for describing derived graphs: how they were
computed, under which assumptions, and what they conclude (§4).

---

## 2. Compatibility and migration

### 2.1 What is guaranteed

**No entity has been removed.** Every 1.0 IRI still exists with the same type,
so a graph annotated with 1.0 still loads and stays consistent under 2.0. The
namespace (`https://w3id.org/def/norma-o#`) and the preferred prefix (`norma`)
are unchanged.

### 2.2 Changes that need action

**`norma:UnderReview` moves to the review lifecycle.** In 1.0 it was a
`NormStatus` in `NormStatusScheme`; in 2.0 it is a `ReviewStatus` in
`ReviewStatusScheme`. Reviewing an annotation does not change whether the norm
is in force, so the value belongs to the annotation, between `PendingReview`
and `Approved`. A 1.0 graph that used it with `hasNormStatus` stays consistent
but is no longer correct:

```turtle
# 1.0
:OBL_x norma:hasNormStatus norma:UnderReview .

# 2.0
:OBL_x norma:hasNormStatus norma:Active ;          # or whatever lifecycle value applies
       norma:hasReviewStatus norma:UnderReview .
```

**`norma:exception` is deprecated** (`owl:deprecated true`). A literal cannot
carry a condition, provenance or a place in the prevalence graph, and it cannot
itself be excepted. Model the carve-out as a norm and link it with a defeater,
or with the `isExceptionTo` shortcut when no condition is needed:

```turtle
# 1.0
:OBL_x norma:exception "Does not apply to systems used for research." .

# 2.0, shortcut: unconditional
:FCT_research a norma:ConstitutiveRule ;
    norma:factStatement "Does not apply to systems used for research." ;
    norma:isExceptionTo :OBL_x .

# 2.0, reified: conditional, with its own gate
:FCT_research a norma:ConstitutiveRule ;
    norma:factStatement "Does not apply to systems used for research." .
:d_research a norma:ExceptionDefeater ;
    norma:defeatingNorm :FCT_research ;
    norma:defeatedNorm  :OBL_x ;
    norma:appliesWhen   :TE_used_for_research_true .
```

The literal is kept for graphs already published and as a last resort for
carve-outs not yet analysed.

### 2.3 Changes to modelling guidance

| Guidance | Why |
|---|---|
| In a `Prohibition`, annotate the **positive** action X (`hasLegalAction`, `actionText`). | The operator already carries the negation. An action text such as "must not develop" inside a prohibition reads as F(¬X) ≡ O(X). |
| Scope carve-outs ("this Regulation does not apply to…") are **`ConstitutiveRule`**, not `Permission`. | A carve-out delimits the field of application without granting any liberty. As a permission it would assert a strong permission the source does not grant. |
| Prefer `hasLegalAction` to the `actionText` shortcut as soon as norms must be compared. | The derivation does not read `actionText`, `agentText`, `objectText`, `conditionTrigger` or the `from…` literals. A norm with only `actionText` falls out of the closure, confers no position and blocks no weak permission. |
| **Align actions across annotators.** | Every inference across norms joins on `LegalAction`. Two individuals minted for the same conduct produce two unrelated islands, and the derivation silently finds nothing. Use `owl:sameAs`, or draw actions from an agreed vocabulary. |
| Name the counterparty (`hasCounterparty`) where the source does. | Without it no correlative Claim or No-right is derived, and comparisons fall back on the `OpenCounterparty` reading (§4.3). |
| Type addressees as `LegalRole` and concrete entities as `LegalParty`. | Real legislation addresses roles. `LegalAgent` remains valid for annotations that commit to neither. |

### 2.4 What changed in existing 1.0 terms

| 1.0 term | Change in 2.0 |
|---|---|
| `Obligation`, `Prohibition` | Formal `skos:definition` in SDL and Hohfeld. New restrictions: each confers some `Duty`; confers only `Duty` or `Claim`; is equivalent only to an `Obligation` or `Prohibition`; contradicts only a `Permission`. |
| `Permission` | Formal definition. Confers some `Privilege`; confers only `Privilege` or `NoRight`; is equivalent only to a `Permission`; contradicts only an `Obligation` or `Prohibition`. New subclass `Facultative`. |
| `Recommendation`, `NegativeRecommendation` | Formal definition. Confer no legal position (`maxCardinality 0` on `confersLegalPosition`), because neither binds; equivalent only to a `Recommendation` or `NegativeRecommendation`. |
| `RegulativeNorm` | Scope note grounding the subclasses in SDL, and explaining why interdefinability is not asserted as class equivalence (it would collapse the disjoint subclasses). |
| `ConstitutiveRule` | Gains `confersRole` and `establishesTrigger`. New scope notes: the Searle reading and scope carve-outs. |
| `LegalAgent` | New disjoint subclasses `LegalRole` and `LegalParty`. |
| `LegalAction` | New scope note on aligning actions across annotators. |
| `TriggerEvent` | Now also the target of `holdsTrigger` (cases), `appliesWhen` (defeaters) and `establishesTrigger` (institutional facts). |
| `LegalSource` | Gains `hasRank`. |
| `supersedes` | Now a subproperty of `temporalPrevailsOver` and `directlyPrevailsOver`, so existing supersessions enter the prevalence graph. |
| `UnderReview` | Moved to `ReviewStatus` (§2.2). |
| `exception` | Deprecated (§2.2). |
| `sanction` | Scope note: a literal only; the violation of a norm is not computable in this version. |
| `deonticId`, `conditionStatement`, `hasLegalAction` | Descriptions no longer refer to BPMN or to a specific pipeline. |
| Top-level classes | The 1.0 disjointness of top-level classes is extended to `LegalPosition`, `Defeater`, `FactPattern`, `WeakPermission` and `RoleAssignment` (eleven pairwise disjoint classes). |

### 2.5 Migration checklist for a 1.0 graph

1. Update `owl:imports` to `https://w3id.org/def/norma-o` (latest) or pin
   `https://w3id.org/def/norma-o/2.0`.
2. Reassign `UnderReview` from `hasNormStatus` to `hasReviewStatus`.
3. Turn `exception` literals into norms plus `isExceptionTo` or an
   `ExceptionDefeater`, where the carve-out matters for evaluation.
4. Check prohibitions whose action text is already negative.
5. Re-type scope carve-outs annotated as `Permission` as `ConstitutiveRule`.
6. Retype addressees as `LegalRole` where they are roles.
7. Add `hasCounterparty` where the source names one.
8. Run a reasoner: the new restrictions may reveal inconsistencies 1.0 could
   not see.

---

## 3. New modelling layers

### 3.1 Standard Deontic Logic: actions, their negation and the closure

- **`norma:isNegationOf`** links an action X to the action ¬X of not doing X.
  It is functional, symmetric and irreflexive. It is what lets the ontology
  state F(X) ≡ O(¬X) and P(X) ≡ ¬O(¬X).
- **`norma:Facultative`** (subclass of `Permission`) is P(X) ∧ P(¬X): X is
  neither obligatory nor forbidden. It confers at least two privileges
  (`minQualifiedCardinality 2`), one over X and one over ¬X.
- **Eight `entails…` properties** record the deontic closure of a norm, from
  `RegulativeNorm` to `LegalAction`:

  | Property | Reads |
  |---|---|
  | `entailsObligatory` / `entailsNotObligatory` | O(x) / ¬O(x) |
  | `entailsPermitted` / `entailsNotPermitted` | P(x) / ¬P(x) |
  | `entailsForbidden` / `entailsNotForbidden` | F(x) / ¬F(x) |
  | `entailsRecommended` / `entailsDiscouraged` | Rec(x) / NegRec(x) |

  `entailsPermitted ≡ entailsNotForbidden` and `entailsNotPermitted ≡
  entailsForbidden` are declared `owl:equivalentProperty`.
  `entailsObligatory` is disjoint with `entailsNotObligatory`, and
  `entailsPermitted` with `entailsNotPermitted`, so a norm whose closure
  contains both O(x) and ¬O(x) makes the graph inconsistent. These properties
  are **derived, never annotated**: the closure is produced by the rule set
  (§5.2), because OWL 2 DL cannot express it.
- **`norma:WeakPermission`** is weak permission in the sense of von Wright and
  of Alchourrón and Bulygin: X is not forbidden for an agent in a case simply
  because no applicable norm forbids it. It is distinct from strong permission
  (an enacted `Permission`), disjoint from `NormativeContent` because it has no
  source and no text, and always relative to a case. Each one has exactly one
  `aboutAction`, one `forAgent` and one `inFactPattern`.

### 3.2 Deontic relations between norms

| Property | Characteristics | Meaning | Example |
|---|---|---|---|
| `isDeonticallyEquivalentTo` | symmetric, transitive | same deontic content for the same agent, counterparty and circumstances, under different operators | F(¬x) and O(x) |
| `deonticallyContradicts` | symmetric, irreflexive; subproperty of `deonticallyConflictsWith` | contents are each other's negation: exactly one holds | P(x) and F(x); P(¬x) and O(x) |
| `deonticallyConflictsWith` | symmetric, irreflexive | both cannot hold, though both may fail | O(x) and F(x) |

Class restrictions keep each relation within compatible operator families: an
`Obligation` or `Prohibition` contradicts only a `Permission`, and is
equivalent only to an `Obligation` or `Prohibition`.

These relations are **prima facie**: they hold between the norms as enacted and
do not consult their status in a case. Two equivalent norms stay equivalent
even where an exception defeats one of them.

### 3.3 Hohfeldian legal positions

**`norma:LegalPosition`** is a directed, first-order jural relation held by one
legal agent (the holder, A) against another (the counterparty, B) and
concerning an action or its negation. It has four pairwise disjoint subclasses
arranged in Hohfeld's square:

```
            correlative
   Duty(A→B, x) ─────────── Claim(B→A, x)
        │                        │
 jural  │                        │  jural
opposite│                        │ opposite
        │                        │
 Privilege(A→B, ¬x) ───── NoRight(B→A, ¬x)
            correlative
```

| Property | From → to | Characteristics |
|---|---|---|
| `confersLegalPosition` | norm → position | |
| `hasPositionHolder` | position → agent (A) | functional |
| `hasPositionCounterparty` | position → agent (B) | defined by a chain (see below) |
| `concernsLegalAction` | position → action | |
| `isCorrelativeOf` | position ↔ position | functional, symmetric, irreflexive |
| `isJuralOppositeOf` | position ↔ position | symmetric, irreflexive |
| `hasCounterparty` | regulative norm → agent | |

Each has an inverse (Appendix A).

**What each kind of norm confers:**

| Norm | Confers |
|---|---|
| `Obligation` of x | a `Duty` of A toward B over x, and its correlative `Claim` of B |
| `Prohibition` of x | a `Duty` of A toward B over ¬x, and its `Claim` |
| `Permission` of x | a `Privilege` of A toward B over x, and its correlative `NoRight` of B |
| `Facultative` x | two privileges, over x and over ¬x |
| `Recommendation`, `NegativeRecommendation` | nothing |

Positions are **directed**. Two positions are jural opposites only if they share
both the holder **and** the counterparty. An agent may owe X to B while being
at liberty to omit X as against C: that is Hohfeld's multital analysis, two
distinct jural relations, not a contradiction.

Positions are also **prima facie**: they are conferred by the norm as enacted.
"A bears a duty toward B concerning X" is what the provision establishes, not
what A owes in a given case; whether the duty bites is settled by evaluating
the case (§5.2, stage 6).

`hasCounterparty` is what makes correlatives possible. Without it, a derived
Duty has no Claim: no party B is ever invented.

### 3.4 Roles, parties and cases

| Term | Meaning |
|---|---|
| `LegalRole` | the abstract addressee a source names: provider, deployer, importer… |
| `LegalParty` | a concrete natural or legal person, authority or body |
| `RoleAssignment` | the fact that a party occupies a role in a case: exactly one `hasAssignedParty`, exactly one `hasAssignedRole`, and the rule it rests on, `assignedUnderRule` |
| `FactPattern` | a described case: the trigger events that fire in it (`holdsTrigger`) and the role assignments that hold (`holdsRoleAssignment`) |
| `confersRole` | the role a constitutive rule attributes: Searle's "X counts as Y in context C" |

`LegalRole` and `LegalParty` are disjoint subclasses of `LegalAgent`. A trigger
event is a condition together with the outcome it takes, so `holdsTrigger`
states, for example, "substantial modification = yes" in this case.

```turtle
:FCT_Art25_1_counts_as_provider a norma:ConstitutiveRule ;
    norma:confersRole :Role_Provider .

:OBL_Art16_provider a norma:Obligation ;
    norma:hasLegalAgent :Role_Provider ;          # addressed to the ROLE
    norma:hasLegalAction :Action_comply_art16 .

:Case_acme_modified a norma:FactPattern ;
    norma:holdsTrigger :TE_art25_1b ;             # substantial modification = yes
    norma:holdsRoleAssignment :RA_acme_provider .

:RA_acme_provider a norma:RoleAssignment ;
    norma:hasAssignedParty :Party_Acme ;          # the concrete PARTY
    norma:hasAssignedRole  :Role_Provider ;
    norma:assignedUnderRule :FCT_Art25_1_counts_as_provider .
```

The role assignment is **asserted, not derived**. This is the one place where
the ontology departs from its principle of deriving what is not generative. The
obstacle is that a `TriggerEvent` records *what* happened, not *who* did it, so
nothing in the graph connects a rule's circumstances to a party. Because the
assignment is asserted and never retracted, the rule set **warns** when a case
holds an assignment whose justifying rule does not apply there (§5.3).

The assignment is case-relative, which is why it is reified: the same party
occupies different roles in different cases. It is not itself defeasible.

### 3.5 Defeasibility: exceptions, conflicts and repeal

**`norma:Defeater`** is a reified defeat relation. It is the **edge**, and the
norms are what defeat one another, so it is disjoint from `NormativeContent`.
Each has at least one `defeatingNorm` and at least one `defeatedNorm`.

| Class | Kind of defeat | Scope | Effect |
|---|---|---|---|
| `ExceptionDefeater` | undercutting (Pollock) | conditional, case-dependent | withdraws the norm's effect without asserting the opposite status |
| `ConflictDefeater` | rebutting | conditional, case-dependent | the defeating norm asserts an opposing status and prevails by a priority principle |
| `TemporalDefeater` | repeal (*lex posterior*) | total | the defeated norm leaves the normative system; bears on validity, not applicability |

**Parts of a defeater**

- `defeatingNorm` / `defeatedNorm`. `defeatedNorm` is not functional, because a
  single repeal may withdraw a block of norms.
- `appliesWhen`: the `TriggerEvent` that gates the defeater. The gates of one
  defeater are read conjunctively; alternative defeaters disjunctively.
- `hasResolutionPrinciple` (on a `ConflictDefeater`): `LexSuperior`,
  `LexSpecialis`, `LexPosterior`. Not functional: several principles may be
  invoked, even pointing in opposite directions.

**Shortcuts without a reified defeater:** `isExceptionTo` (subproperty of
`exceptionPrevailsOver` and `directlyPrevailsOver`) and `supersedes`
(subproperty of `temporalPrevailsOver` and `directlyPrevailsOver`). They carry
no gate, so they are unconditional. Reify a defeater when the defeat needs a
condition, provenance, a principle or several defeated norms.

**Hierarchy of sources.** `NormativeRank`, assigned to a source with `hasRank`
and copied onto a norm with `fromRank`:

| Rank | `rankLevel` |
|---|---:|
| `ConstitutionalRank` | 40 |
| `LegislativeRank` | 30 |
| `RegulatoryRank` | 20 |
| `DelegatedRank` | 10 |
| `OrganisationalRank` | 0 |

A higher level prevails over a lower one. The integer makes *lex superior*
computable by comparison within one legal order.

**Norm strength.** `NormStrength` with `Strict` (admits no defeat) and
`Defeasible` (the default when nothing is stated), via `hasNormStrength`.
Defeating a `Strict` norm is reported as an annotation contradiction and has
no effect.

**The prevalence graph:**

```
prevailsOver  (≡ isDefeatingNormOf ∘ defeatedNorm)
├── directlyPrevailsOver      asymmetric, irreflexive
│   ├── isExceptionTo
│   └── supersedes
├── exceptionPrevailsOver     ⊒ isExceptionTo
├── conflictPrevailsOver
└── temporalPrevailsOver      ⊒ supersedes
```

The chain that defines `prevailsOver` drops the gate, so `prevailsOver` is the
static, unconditional projection. Case evaluation must traverse the reified
defeater.

Because an exception is now a norm with a node of its own, **it can be excepted
in turn**, which a literal could never express (Article 6(3) of the AI Act is
the example in §6.2).

### 3.6 Counts-as chaining

A constitutive rule concludes an institutional fact, and regulative norms are
often conditioned on that fact. **`norma:establishesTrigger`** (inverse
`isTriggerEstablishedBy`) links normative content to a trigger event that
**holds whenever that content applies**. The norms conditioned on the rule's
conclusion become activated by it.

This closes a gap that produced a legally wrong result. Article 6(2) of
Regulation (EU) 2024/1689 classifies Annex III systems as high-risk, and
Articles 16 and 26 bind the providers and deployers *of high-risk systems*.
Article 6(3) does not except a system from Article 16: it excepts it from the
**classification**. Wiring the exception straight to Article 16 skips a rung
and leaves the Article 26 deployer obligations applicable to a system that is
not high-risk. With the chaining, defeating the classification withdraws both
obligations, and reinstating the classification reinstates both (§6.2).

The institutional fact must be **established by a rule, not annotated in the
case**. A fact asserted in a `FactPattern` is brute and no defeater can touch
it; an institutional fact is defeasible.

`confersRole` covers the counts-as that attributes a *role*;
`establishesTrigger` covers the counts-as that establishes a *fact*.

---

## 4. The derivation module `normad`

`https://w3id.org/def/norma-o/deriv` describes **derived graphs**: what was
computed, by which rule set, and under which assumptions. A derived graph is
regenerated, never maintained, and must never be merged back into the
annotation graph. The full catalogue is in Appendix B.

### 4.1 Classes

| Class | Purpose |
|---|---|
| `DerivationActivity` (⊑ `prov:Activity`) | one run of a rule set; must declare at least one assumption |
| `PrevalenceOrdering` | the ladder computed for the static projection or for one case |
| `NormEvaluation` | the outcome for one norm within one ordering: its level and, per case, its status and reach |
| `PrevalenceCycle` | a cycle found in the defeat digraph, reported rather than resolved |
| `ApplicabilityStatus`, `Assumption`, `CycleKind` | SKOS value classes, each with its concept scheme |

### 4.2 Applicability statuses

| Status | Meaning |
|---|---|
| `Invalid` | not a member of the normative system: superseded, not yet in force, or repealed. Case-independent. |
| `NotActivated` | valid, but none of the trigger events that activate it fires in the case |
| `Applicable` | valid, activated, and every defeater reaching it is itself defeated, or none reaches it |
| `Defeated` | valid and activated, but an applicable norm defeats it |
| `Undecided` | the asserted defeaters do not fix a label: the grounded fixpoint leaves it open |

The scheme is about **applicability, not being in force**: in legal usage a
norm is in force as a matter of temporal validity, whereas what a case decides
is whether the norm reaches it.

### 4.3 Assumptions

A derived conclusion is only meaningful together with the readings it rests
on. Each `DerivationActivity` states them with `computedUnderAssumption`:

| Assumption | Reading | Declared by the reference rule set |
|---|---|---|
| `ClosedGraph` | a norm absent from the graph is absent from the system | always |
| `ClosedCaseDescription` | a condition the case is silent about does not hold | always |
| `DefeatConsidered` | defeat relations were taken into account | always |
| `GroundedSemantics` | defeat evaluated under Dung's grounded semantics | always |
| `InstitutionalFactsChained` | facts established by applicable constitutive rules were fed back into the case | when the graph uses `establishesTrigger` |
| `OpenCounterparty` | an unnamed counterparty is read as not disagreeing when norms or positions are compared | when some norm with an action names no counterparty |
| `DefeatNotConsidered` | defeat relations were ignored | never (available to other producers) |
| `ReinstatementNotComputed` | defeat applied one level deep, without reinstatement | never (available to other producers) |

### 4.4 Cycle kinds

| Kind | When |
|---|---|
| `SecondDegreeConflict` | conflict defeaters on the cycle cite **different** principles: the criteria themselves are unordered for that pair (Bobbio) |
| `AnnotationContradiction` | conflict defeaters cite the **same** principle in opposite directions, which one principle cannot sustain |
| `IrresolubleAntinomy` | the defeat cites no principle at all, typically a loop of exceptions |

---

## 5. What can now be derived

There are two sources of inference, and they do different things.

### 5.1 With a standard OWL 2 DL reasoner (HermiT, Pellet…)

| Inference | Mechanism |
|---|---|
| The counterparty of a position: if A bears a Duty toward B, the Claim is B's against A | `hasPositionCounterparty ⊒ isCorrelativeOf ∘ hasPositionHolder` |
| The content of the correlative position | `concernsLegalAction ⊒ isCorrelativeOf ∘ concernsLegalAction` |
| "B prevails over A" from a reified `Defeater` | `prevailsOver ⊒ isDefeatingNormOf ∘ defeatedNorm` |
| Supersessions and exceptions asserted as shortcuts enter the prevalence graph | `supersedes ⊑ temporalPrevailsOver`, `isExceptionTo ⊑ exceptionPrevailsOver` |
| P(x) and ¬F(x) are interchangeable, as are ¬P(x) and F(x) | `owl:equivalentProperty` |
| Inverses of every new relation, symmetry of `isNegationOf`, `isCorrelativeOf` and the deontic relations, transitivity of `isDeonticallyEquivalentTo` | property characteristics |

The 1.0 chain `triggersNorm ⊒ hasTrigger ∘ activatesNorm` is kept.

**Inconsistencies a reasoner now detects:**

- an individual typed as two of the four positions, two of the three defeater
  kinds, both `LegalRole` and `LegalParty`, or two of the eleven top-level
  classes;
- a norm whose closure contains both O(x) and ¬O(x), or both P(x) and ¬P(x);
- an `Obligation` or `Prohibition` stated to contradict another `Obligation` or
  `Prohibition` (the restriction would type the other end as a `Permission`,
  which is disjoint), or a recommendation stated to confer a position;
- A directly prevailing over B and B directly over A, or a norm directly
  prevailing over itself.

The functional properties (`hasAssignedParty`, `aboutAction`,
`hasPositionHolder`…) do not by themselves make a second value inconsistent:
OWL has no unique-name assumption, so a reasoner concludes that the two values
are the same individual (`owl:sameAs`). The clash surfaces only if they are
declared different or belong to disjoint classes.

### 5.2 With the reference rule set (`deriv/`)

Some semantics the ontology declares cannot be expressed in OWL 2 DL:

- **the deontic closure**: the equivalences that flip the action would need
  property chains over `isNegationOf` in both directions, which violates the
  regularity condition and would make the `entails…` properties non-simple, so
  they could no longer be declared disjoint;
- **the Hohfeldian positions**: minting them means creating individuals, which
  no reasoner does;
- **the prevalence ordering**: full acyclicity is not expressible;
- **counts-as chaining**: an iteration to a fixpoint, not an entailment.

`deriv/derive.py` computes these with **19 SPARQL rules** and the graph
algorithms in `deriv/prevalence.py`. It needs no reasoner and materialises both
directions of every symmetric relation, so the output can be queried directly.

| Rule file | Stage | Does |
|---|---|---|
| `01-action-negation.rq` | 1 | mints ¬X for every regulated action without one |
| `01b-negation-symmetry.rq` | 1 | completes `isNegationOf` where only one direction is asserted |
| `02a-closure-obligation.rq` | 2 | closure of O(x) |
| `02b-closure-prohibition.rq` | 2 | closure of F(x) |
| `02c-closure-permission.rq` | 2 | closure of P(x) |
| `02d-closure-facultative.rq` | 2 | adds the P(¬x) half of a facultative norm |
| `02e-closure-recommendation.rq` | 2 | closure of Rec(x) |
| `02f-closure-negative-recommendation.rq` | 2 | closure of NegRec(x) |
| `03a-defeat-edges.rq` | 3 | defeat edges from reified defeaters, with kind, gate and principle |
| `03a-defeat-shortcuts.rq` | 3 | defeat edges from `isExceptionTo`, `supersedes`, `supersededBy` |
| `03b-wp-candidates.rq` | 3 | candidate (agent, action, case) triples for weak permission |
| `03c-wp-blocked.rq` | 3 | prohibitions that could block each candidate |
| `04a-position-duty.rq` | 4 | Duty and its Claim |
| `04b-position-privilege.rq` | 4 | Privilege and its No-right |
| `04c-jural-opposite.rq` | 4 | opposition on the Duty ⟷ Privilege axis |
| `04d-jural-opposite-correlatives.rq` | 4 | opposition on the Claim ⟷ No-right axis |
| `05a-deontic-equivalence.rq` | 5 | `isDeonticallyEquivalentTo` |
| `05b-deontic-contradiction.rq` | 5 | `deonticallyContradicts` |
| `05c-deontic-contrariety.rq` | 5 | `deonticallyConflictsWith` for contrary pairs |

#### Stage 1 — Action negation

Mints ¬X with a deterministic IRI (`<X>_neg`) and asserts both directions of
`isNegationOf`. The label `"not …"@en` is built only from an English label;
with no English label the negation is minted without one rather than with a
label in the wrong language.

#### Stage 2 — SDL closure

| Norm | Entails |
|---|---|
| O(x) | O(x), P(x) (axiom D), ¬F(x), F(¬x), ¬P(¬x), ¬O(¬x) |
| F(x) | F(x), ¬P(x), ¬O(x), O(¬x), P(¬x), ¬F(¬x) |
| P(x) | only P(x), ¬F(x), ¬O(¬x). O(x), P(¬x) and F(¬x) are deliberately left **open** |
| Facultative(x) | what P(x) gives, plus P(¬x), ¬F(¬x), ¬O(x) |
| Rec(x) | Rec(x), NegRec(¬x). No analogue of axiom D |
| NegRec(x) | NegRec(x), Rec(¬x) |

#### Stage 3 — Defeat graph and weak permission

Extracts every defeat edge with its kind, gate and principle. Generates a
**`WeakPermission`** for each (agent, action, case) that the graph mentions and
leaves unblocked. A weak permission is blocked if some norm forbidding the
action for that agent is `Applicable` **or `Undecided`** in the case: the
reading is sceptical, because while the fate of a prohibition is not settled it
cannot be asserted that the action is not forbidden. `Invalid` and
`NotActivated` prohibitions do not block.

#### Stage 4 — Hohfeldian positions

`entailsObligatory` yields a **Duty** of the agent and, if the norm names a
counterparty, the correlative **Claim**. It fires only for obligations and
prohibitions, and for a prohibition it already works over the negated action,
so the content of the duty is right in both cases. An enacted permission yields
a **Privilege** and, with a counterparty, its **NoRight**; no privilege is
minted from an obligation even though it entails P(x). `isJuralOppositeOf` is
derived on both axes, requiring the same holder and the same counterparty, and
excluding norms activated by opposite branches of one condition.

#### Stage 5 — Relations between norms

Norms are joined on the same agent, a non-disagreeing counterparty and
compatible activation conditions. Identical closures give
`isDeonticallyEquivalentTo`; a P(y)/¬P(y) pair starting from a permission gives
`deonticallyContradicts` (and its superproperty); a contrary pair gives
`deonticallyConflictsWith`. Two norms activated by **opposite branches of one
condition** never meet in a case and are excluded.

> **Stages 4 and 5 are prima facie.** They work on norms as enacted and never
> consult their status in a case. A compliance answer joins them with stage 6.

#### Stage 6 — Validity, prevalence and applicability

**Validity first.** Out of the system go norms that are `Superseded` or
`NotYetInForce`, those with `supersededBy`, and those repealed by a
`TemporalDefeater` whose repealing norm is itself valid. Repeal is applied
**flatly**: repealing a repealing norm does not revive what it repealed,
whereas a norm merely set aside by an exception is reinstated when the
exception falls, because it never left the system. This follows the civil-law
default (e.g. art. 2.2 of the Spanish Civil Code) and is documented in the
module.

Over the valid norms and the exception and conflict edges, four things are
computed, by separate functions because they answer separate questions:

1. **`kahn()`** — layered topological order, by longest path, so the level does
   not depend on traversal order. Nodes it cannot order are on a cycle or
   downstream of one: this is the cycle detection.
2. **`cycles()`** — the non-trivial strongly connected components (Kosaraju),
   so that each cycle can be **reported** (`PrevalenceCycle`, `inCycle`,
   `involvesNorm`), classified (`hasCycleKind`) and its competing principles
   listed (`citesCompetingPrinciple`).
3. **`strata()`** — the published levels (`prevalenceLevel`, `stratumCount`),
   computed on the **condensation** of the digraph into strongly connected
   components. Every norm gets a rung; the norms of one cycle share theirs; and
   the acyclic descendants of a cycle are not left without a level.
4. **`grounded()`** — Dung's grounded labelling, a monotone fixpoint: a norm
   holds if all its attackers are withdrawn, and is withdrawn if any attacker
   holds. `Strict` norms lose their incoming edges first. This is what gives
   **reinstatement**.

> The ordering **orders; it does not decide cases.** A single pass in
> topological order is wrong downstream of a cycle: if an undefeated *c*
> withdraws both norms of a cycle *a ⟷ a′*, and *a* attacked *b*, then *b*
> holds. Applicability always comes from `grounded()`, and lying on a cycle does
> not by itself leave a norm undecided.

Everything is computed **once statically** (`ordering_static`, the ungated
projection, with levels but no statuses) and **once per `FactPattern`**,
keeping only the defeaters whose gates fire and whose defeating norm is
activated in that case.

Per case, evaluation **alternates** with counts-as chaining: the facts
established by applicable constitutive rules are added to the case, the norms
are evaluated again, and so on until no new fact appears. The set of facts only
grows, so this terminates.

Each norm then receives one `hasApplicabilityStatus`, by precedence: validity
(`Invalid`), then activation (`NotActivated`), then the grounded label.

**Reach.** `reachesParty` states which concrete party a norm reaches in the
case: a norm addressed to a role reaches whoever the case places in that role,
and a norm addressed to a party reaches that party. Reach is emitted whatever
the status; a consumer joins reach and applicability.

### 5.3 What the rule set reports

Besides the derived graph, `derive.py` prints warnings for what it cannot
resolve or what looks wrong in the annotation:

| Warning | Meaning |
|---|---|
| `CYCLE (<kind>)` | a prevalence cycle, with its kind and competing principles |
| `defeat(s) against a Strict norm` | an annotation contradiction; the defeat has no effect |
| `norm(s) outside the system` | invalid norms (repealed, superseded or not yet in force) |
| `role assignment … cites …, which is <status> there` | an asserted role assignment whose justifying rule does not apply in the case |
| `fact … stayed in the case but no rule establishing it turned out applicable` | an institutional fact whose rule was later withdrawn |
| `norm(s) without norma:hasCounterparty` | positions without a materialised correlative |
| `norm(s) without norma:LegalAction` | norms left outside the closure because they only have `actionText` |

### 5.4 Provenance and reproducibility

Each run is a `DerivationActivity` with `ruleSetVersion`, `derivedGraph`,
`prov:used` for each input file and the assumptions of §4.3. Every ordering is
linked to it with `prov:wasGeneratedBy`. The activity IRI is a hash of the
inputs and the rule-set version.

Two runs with the same rule-set version over the same input produce the same
graph, byte for byte in the sorted `.nt` output. Any change to the output
requires bumping `RULE_SET_VERSION`.

---

## 6. Worked examples

All three are test fixtures in `deriv/tests/`, and the outputs below are what
`derive.py` produces for them.

### 6.1 Closure and positions

An obligation of A toward B over `act_o` (`test-abox.ttl`):

```turtle
:n_obl a norma:Obligation ;
    norma:hasLegalAgent :A ; norma:hasCounterparty :B ;
    norma:hasLegalAction :act_o .
```

Derived:

```turtle
:n_obl norma:entailsObligatory :act_o ;
    norma:entailsPermitted :act_o ;
    norma:entailsNotForbidden :act_o ;
    norma:entailsForbidden :act_o_neg ;
    norma:entailsNotPermitted :act_o_neg ;
    norma:entailsNotObligatory :act_o_neg ;
    norma:confersLegalPosition :n_obl_duty_act_o, :n_obl_claim_act_o_B .

:n_obl_duty_act_o a norma:Duty ;
    rdfs:label "duty concerning act_o"@en ;
    norma:hasPositionHolder :A ;
    norma:concernsLegalAction :act_o ;
    norma:isCorrelativeOf :n_obl_claim_act_o_B .

:n_obl_claim_act_o_B a norma:Claim ;
    norma:hasPositionHolder :B ;
    norma:isCorrelativeOf :n_obl_duty_act_o .
```

The Claim's counterparty and content are not materialised: a reasoner infers
them through the chains of §5.1.

### 6.2 Counts-as chaining: Article 6 of the AI Act

`test-counts-as.ttl` reproduces the real structure:

```
 FCT 6(2): Annex III counts as high-risk  ◄──defeats── FCT 6(3): narrow procedural task
      │ establishesTrigger                                   ▲
      ▼                                                      │ defeats
 "is high-risk" = yes                          FCT 6(3) final: profiling
      ├──► activates OBL Art. 16 (provider)
      └──► activates OBL Art. 26 (deployer)
```

No case annotates "is high-risk": each case holds only brute facts.

| Case (brute facts) | 6(2) | 6(3) | 6(3) final | Art. 16 | Art. 26 |
|---|---|---|---|---|---|
| Annex III | Applicable | NotActivated | NotActivated | **Applicable** | **Applicable** |
| Annex III + narrow task | **Defeated** | Applicable | NotActivated | **NotActivated** | **NotActivated** |
| Annex III + narrow task + profiling | Applicable (reinstated) | **Defeated** | Applicable | **Applicable** | **Applicable** |

Defeating the classification withdraws **both** obligations, and the final
subparagraph reinstates both, through the classification. The static ladder
has three strata: the profiling rule and the obligations at level 0, 6(3) at
level 1, 6(2) at level 2.

### 6.3 Roles and reach: Article 25 of the AI Act

`test-roles-art25.ttl`: Acme deploys a high-risk system. Article 16 is
addressed to the role *provider*, Article 26 to the role *deployer*, and
Article 25(1)(b) makes whoever substantially modifies the system count as
provider.

| Case | Art. 25(1) | Reaches Acme |
|---|---|---|
| Acme substantially modified the system | Applicable | Art. 16 and Art. 26 |
| Control: no modification | NotActivated | Art. 26 only |

The derived evaluation for Article 16 in the first case:

```turtle
<…/derived#ordering_Case_acme_modified_eval_OBL_Art16_provider> a normad:NormEvaluation ;
    normad:evaluatedNorm art25:OBL_Art16_provider ;
    normad:inOrdering <…/derived#ordering_Case_acme_modified> ;
    normad:prevalenceLevel 0 ;
    normad:hasApplicabilityStatus normad:Applicable ;
    normad:reachesParty art25:Party_Acme .
```

The activity declares `OpenCounterparty`, because neither obligation names a
counterparty, and warns that their duties have no correlative.

### 6.4 Cycles, Strict norms and chained repeal

`test-cycles.ttl` yields, in its single case:

| Norms | Status | Why |
|---|---|---|
| `n_s1`, `n_s2` | Undecided | cycle of conflict defeaters citing `LexSpecialis` and `LexPosterior`: **SecondDegreeConflict** |
| `n_t1`, `n_t2` | Undecided | cycle citing `LexSuperior` both ways: **AnnotationContradiction** |
| `n_u1`, `n_u2` | Undecided | loop of exceptions with no principle: **IrresolubleAntinomy** |
| `n_v` | Applicable | `Strict`; the defeat against it is reported and void |
| `n_w2`, `n_w3` | Invalid | w1 repeals w2, which had repealed w3: no revival |

---

## 7. Questions 1.0 could not answer

| Question | Answered by |
|---|---|
| Do these two provisions say the same thing in different words? | `isDeonticallyEquivalentTo` |
| Do they contradict each other, or are they merely incompatible? | `deonticallyContradicts`, `deonticallyConflictsWith` |
| What duties and rights does each party have, and toward whom? | `Duty`, `Claim`, `Privilege`, `NoRight` with holder and counterparty |
| In this case, which norms apply after exceptions, conflicts and repeals? | `hasApplicabilityStatus` per `FactPattern` |
| Why does this norm not apply here? | `Invalid`, `NotActivated`, `Defeated` or `Undecided`, with the defeaters that reach it |
| Does this obligation reach this company, given the role it occupies in the case? | `RoleAssignment` + `reachesParty` |
| If a classification is excepted, which obligations fall with it? | `establishesTrigger` + case evaluation |
| What is the prevalence hierarchy of my corpus? | `prevalenceLevel`, `stratumCount` |
| Are there prevalence cycles, and of what kind? | `isAcyclic`, `PrevalenceCycle`, `hasCycleKind`, `citesCompetingPrinciple` |
| May this agent do X because nothing forbids it? | `WeakPermission` |
| Under which assumptions was a conclusion computed? | `computedUnderAssumption` |

---

## 8. Tooling

### 8.1 `deriv/derive.py`

```bash
pip install -r deriv/requirements.txt    # rdflib; owlready2 only for the checks

python deriv/derive.py <abox.ttl> [<cases.ttl> …] [<rules.owl>] -o out.ttl
#   --base <IRI>    base IRI for the derived individuals
#   --timestamp     adds prov:startedAtTime (breaks byte-for-byte comparison)
```

- **Inputs** may be given in any order and are recognised **by content, not by
  extension**. A file containing SWRL atoms is read as a rule artefact, and only
  its `norma:activatesNorm` links are taken from the rule heads. Any other file,
  Turtle or RDF/XML, is loaded whole as an ABox.
- **Outputs**: the derived graph in `out.ttl` and the same graph as sorted
  N-Triples in `out.nt`. Without `-o`, the output goes next to the first input
  as `<input>.derived.ttl`.
- **Base IRI**: by default, `<ABox ontology IRI>/derived#`.
- `prov:used` records each input as an absolute `file:` URI. Bear this in mind
  before publishing a derived graph.
- Needs only `rdflib`. The ontology is found in the folder that contains
  `deriv/`; `NORMA_ONTOLOGY_DIR` points it elsewhere.

### 8.2 `deriv/tests/check_deriv.py` — 140 checks

```bash
python deriv/tests/check_deriv.py
```

Requires `owlready2` and **Java** for HermiT. The Turtle files are the source
of truth: after editing one, update its `.rdf` so that check RDF1 still finds
the two serialisations isomorphic.

| Family | Checks | Covers |
|---|---:|---|
| closure | 7 | exact closure for each operator: nothing missing, nothing extra |
| T | 13 | weak permission per case, with conditions, defeat and reinstatement |
| D | 14 | static ladder, levels, applicability statuses per case |
| P | 4 | activation filters the attack graph; repealed exceptions do not defeat |
| H | 12 | positions conferred by each operator, correlatives, HermiT inferences |
| J | 10 | jural opposition, directedness, agreement with deontic conflict |
| E | 16 | equivalence, contradiction, contrariety, incompatible conditions |
| OWL | 5 | the OWL 2 DL profile: only simple properties where required |
| K | 12 | cycle kinds, Strict norms, chained repeal |
| A | 18 | `kahn`, `cycles`, `strata` and `grounded` against hand-built graphs |
| R | 9 | roles, parties and reach (Article 25) |
| CA | 8 | counts-as chaining (Article 6) and role-assignment warnings |
| CP | 5 | the `OpenCounterparty` assumption |
| C | 1 | RDF/XML and Turtle inputs give the same derived graph |
| RDF | 1 | Turtle and RDF/XML serialisations isomorphic |
| other | 5 | negations, idempotence, consistency of TBox + module + ABox + derived, integrity |

The test fixtures double as worked examples: `test-abox.ttl`,
`test-cycles.ttl`, `test-roles-art25.ttl`, `test-counts-as.ttl`,
`test-silent-counterparty.ttl` and `test-unsound-role.ttl`.

---

## 9. Known limitations

- **Violation is not computable.** `sanction` is a literal, and
  contrary-to-duty obligations ("if O(x) is violated then O(y)") are not
  represented.
- **Lex superior is comparable but not yet used.** `rankLevel` orders ranks,
  but no conflict is oriented by it automatically.
- **Second-degree conflicts are reported, not resolved** into one ordering per
  admissible policy.
- **Conflicts and weak permission compare roles, not parties.** A clash between
  the duties of two roles that one party occupies in a case (as under Article
  25(1), where a deployer also counts as provider) is not detected.
- **Every inference across norms joins on `LegalAction`**, and the ontology
  offers no mechanism for aligning actions across annotators.
- **Role assignments are asserted, not derived** (§3.4).
- **Counts-as chaining only grows.** A fact established by a rule that is later
  withdrawn stays in the case; it is reported, not undone.
- **Article 25(2)**, which stops treating the original provider as a provider,
  is out of scope.
- **No SHACL shapes yet.** The ontology calls for SHACL in seven places where
  OWL cannot express a constraint (e.g. uniqueness of `deonticId`, cardinality
  of `defeatedNorm`).
- **Second-order Hohfeldian positions** (power, liability, immunity,
  disability) are out of scope.
- **Conflicts across legal orders**, and questions of competence, cannot be
  captured by a single integer rank.

---

## Appendix A — catalogue of new core terms

Namespace `norma:` = `https://w3id.org/def/norma-o#`. Characteristics:
F functional, S symmetric, T transitive, I irreflexive, A asymmetric.

### A.1 Deontic logic (17)

| Term | Kind | Domain → Range | Char. | Definition |
|---|---|---|---|---|
| `Facultative` | class ⊑ `Permission` | | | A permission under which a legal action is optional: permitted both to perform and to omit. |
| `WeakPermission` | class ⊑ `prov:Entity` | | | A derived, case-relative statement that an action is not forbidden for an agent under a described case. |
| `isNegationOf` | object property | `LegalAction` → `LegalAction` | F S I | Links an action X to the action ¬X of not performing it. |
| `entailsObligatory` | object property | `RegulativeNorm` → `LegalAction` | | Derived: O(x). Disjoint with `entailsNotObligatory`. |
| `entailsNotObligatory` | object property | `RegulativeNorm` → `LegalAction` | | Derived: ¬O(x). |
| `entailsPermitted` | object property | `RegulativeNorm` → `LegalAction` | | Derived: P(x). ≡ `entailsNotForbidden`; disjoint with `entailsNotPermitted`. |
| `entailsNotPermitted` | object property | `RegulativeNorm` → `LegalAction` | | Derived: ¬P(x). ≡ `entailsForbidden`. |
| `entailsForbidden` | object property | `RegulativeNorm` → `LegalAction` | | Derived: F(x), equivalently O(¬x). |
| `entailsNotForbidden` | object property | `RegulativeNorm` → `LegalAction` | | Derived: ¬F(x). |
| `entailsRecommended` | object property | `RegulativeNorm` → `LegalAction` | | Derived: the action is recommended. |
| `entailsDiscouraged` | object property | `RegulativeNorm` → `LegalAction` | | Derived: the action is discouraged. |
| `isDeonticallyEquivalentTo` | object property ⊑ `relatesTo` | `RegulativeNorm` → `RegulativeNorm` | S T | Same deontic content for the same agent, counterparty and circumstances, under different operators. |
| `deonticallyConflictsWith` | object property ⊑ `relatesTo` | `RegulativeNorm` → `RegulativeNorm` | S I | The two norms cannot both hold under SDL. |
| `deonticallyContradicts` | object property ⊑ `deonticallyConflictsWith` | `RegulativeNorm` → `RegulativeNorm` | S I | Contents are each other's negation: exactly one holds. |
| `aboutAction` | object property | `WeakPermission` → `LegalAction` | F | The single action a weak permission concerns. |
| `forAgent` | object property | `WeakPermission` → `LegalAgent` | F | The single agent for whom the action is not forbidden. |
| `inFactPattern` | object property | `WeakPermission` → `FactPattern` | F | The single case relative to which it was computed. |

### A.2 Hohfeldian positions (17)

| Term | Kind | Domain → Range | Char. | Definition |
|---|---|---|---|---|
| `LegalPosition` | class | | | A directed first-order jural relation held by a holder against a counterparty, concerning an action or its negation. |
| `Duty` | class ⊑ `LegalPosition` | | | The holder is bound toward the counterparty to realise the content. Correlative: Claim. Opposite: Privilege. |
| `Claim` | class ⊑ `LegalPosition` | | | The holder is entitled, against the counterparty, that the counterparty realise the content. Correlative: Duty. Opposite: No-right. |
| `Privilege` | class ⊑ `LegalPosition` | | | The holder is free, against the counterparty, to realise the content. Correlative: No-right. Opposite: Duty. |
| `NoRight` | class ⊑ `LegalPosition` | | | The holder has no claim that the counterparty refrain. Correlative: Privilege. Opposite: Claim. |
| `confersLegalPosition` | object property | `NormativeContent` → `LegalPosition` | | A position a norm creates. Inverse `isLegalPositionConferredBy`. |
| `isLegalPositionConferredBy` | object property | `LegalPosition` → `NormativeContent` | | Inverse of the above. |
| `hasPositionHolder` | object property | `LegalPosition` → `LegalAgent` | F | A, in "A has a duty toward B". Inverse `isPositionHolderOf`. |
| `isPositionHolderOf` | object property | `LegalAgent` → `LegalPosition` | | Inverse of the above. |
| `hasPositionCounterparty` | object property | `LegalPosition` → `LegalAgent` | | B, in "A has a duty toward B". ⊒ `isCorrelativeOf ∘ hasPositionHolder`. Inverse `isPositionCounterpartyOf`. |
| `isPositionCounterpartyOf` | object property | `LegalAgent` → `LegalPosition` | | Inverse of the above. |
| `concernsLegalAction` | object property | `LegalPosition` → `LegalAction` | | The action that forms the content. ⊒ `isCorrelativeOf ∘ concernsLegalAction`. Inverse `isContentOfLegalPosition`. |
| `isContentOfLegalPosition` | object property | `LegalAction` → `LegalPosition` | | Inverse of the above. |
| `isCorrelativeOf` | object property | `LegalPosition` → `LegalPosition` | F S I | The position necessarily held by the counterparty toward the holder over the same content. |
| `isJuralOppositeOf` | object property | `LegalPosition` → `LegalPosition` | S I | The position of the same holder toward the same counterparty over the negated content. |
| `hasCounterparty` | object property | `RegulativeNorm` → `LegalAgent` | | The agent toward whom the addressee is bound or free. Inverse `isCounterpartyOf`. |
| `isCounterpartyOf` | object property | `LegalAgent` → `RegulativeNorm` | | Inverse of the above. |

### A.3 Roles, parties and cases (16)

| Term | Kind | Domain → Range | Char. | Definition |
|---|---|---|---|---|
| `LegalRole` | class ⊑ `LegalAgent` | | | An abstract addressee defined by a legal source. Disjoint with `LegalParty`. |
| `LegalParty` | class ⊑ `LegalAgent` | | | A concrete natural or legal person, authority, agency or body. |
| `RoleAssignment` | class | | | The fact that a given party occupies a given role. |
| `FactPattern` | class | | | A described case: the trigger events that fire and the roles parties occupy. |
| `confersRole` | object property | `NormativeContent` → `LegalRole` | | The role a norm attributes. Inverse `isRoleConferredBy`. |
| `isRoleConferredBy` | object property | `LegalRole` → `NormativeContent` | | Inverse of the above. |
| `hasAssignedParty` | object property | `RoleAssignment` → `LegalParty` | F | The single party occupying the role. Inverse `isAssignedPartyOf`. |
| `isAssignedPartyOf` | object property | `LegalParty` → `RoleAssignment` | | Inverse of the above. |
| `hasAssignedRole` | object property | `RoleAssignment` → `LegalRole` | F | The single role occupied. Inverse `isAssignedRoleOf`. |
| `isAssignedRoleOf` | object property | `LegalRole` → `RoleAssignment` | | Inverse of the above. |
| `assignedUnderRule` | object property | `RoleAssignment` → `NormativeContent` | | The constitutive rule that justifies the assignment. Inverse `isRuleOfRoleAssignment`. |
| `isRuleOfRoleAssignment` | object property | `NormativeContent` → `RoleAssignment` | | Inverse of the above. |
| `holdsRoleAssignment` | object property | `FactPattern` → `RoleAssignment` | | A role assignment that holds in the case. Inverse `isRoleAssignmentIn`. |
| `isRoleAssignmentIn` | object property | `RoleAssignment` → `FactPattern` | | Inverse of the above. |
| `holdsTrigger` | object property | `FactPattern` → `TriggerEvent` | | A condition and outcome that fire in the case. Inverse `isHeldInFactPattern`. |
| `isHeldInFactPattern` | object property | `TriggerEvent` → `FactPattern` | | Inverse of the above. |

### A.4 Defeasibility (38)

| Term | Kind | Domain → Range | Char. | Definition |
|---|---|---|---|---|
| `Defeater` | class ⊑ `prov:Entity` | | | Reified defeat relation: one norm withdraws or overrides the effect of another. |
| `ExceptionDefeater` | class ⊑ `Defeater` | | | Switches off the defeated norm under a condition, without asserting the opposite status. |
| `ConflictDefeater` | class ⊑ `Defeater` | | | The defeating norm asserts an opposing status and prevails by a priority principle. |
| `TemporalDefeater` | class ⊑ `Defeater` | | | A later norm repeals an earlier one. |
| `NormStrength` | class ⊑ `skos:Concept` | | | Whether a norm admits defeat at all. Scheme `NormStrengthScheme`. |
| `NormativeRank` | class ⊑ `skos:Concept` | | | Rank of a legal source in the hierarchy of sources. Scheme `NormativeRankScheme`. |
| `ResolutionPrinciple` | class ⊑ `skos:Concept` | | | A principle that orients the resolution of a conflict. Scheme `ResolutionPrincipleScheme`. |
| `defeatingNorm` | object property | `Defeater` → `NormativeContent` | | The norm that performs the overriding. Inverse `isDefeatingNormOf`. |
| `isDefeatingNormOf` | object property | `NormativeContent` → `Defeater` | | Inverse of the above. |
| `defeatedNorm` | object property | `Defeater` → `NormativeContent` | | The norm whose effect is withdrawn. Not functional. Inverse `isDefeatedBy`. |
| `isDefeatedBy` | object property | `NormativeContent` → `Defeater` | | Inverse of the above. |
| `appliesWhen` | object property | `Defeater` → `TriggerEvent` | | The gate that activates the defeater. Inverse `isGateOfDefeater`. |
| `isGateOfDefeater` | object property | `TriggerEvent` → `Defeater` | | Inverse of the above. |
| `hasResolutionPrinciple` | object property | `ConflictDefeater` → `ResolutionPrinciple` | | The principle that orients the conflict. Not functional. Inverse `isResolutionPrincipleOf`. |
| `isResolutionPrincipleOf` | object property | `ResolutionPrinciple` → `ConflictDefeater` | | Inverse of the above. |
| `hasRank` | object property | `LegalSource` → `NormativeRank` | F | The rank of a source. Inverse `isRankOf`. |
| `isRankOf` | object property | `NormativeRank` → `LegalSource` | | Inverse of the above. |
| `fromRank` | object property | `NormativeContent` → `NormativeRank` | F | Rank copied onto the norm from its source, like `fromRegulation`. |
| `hasNormStrength` | object property | `NormativeContent` → `NormStrength` | F | Whether the norm admits defeat. Inverse `isNormStrengthOf`. |
| `isNormStrengthOf` | object property | `NormStrength` → `NormativeContent` | | Inverse of the above. |
| `prevailsOver` | object property | `NormativeContent` → `NormativeContent` | | Defeating norm → defeated norm. ⊒ `isDefeatingNormOf ∘ defeatedNorm`. Inverse `isPrevailedOverBy`. |
| `isPrevailedOverBy` | object property | `NormativeContent` → `NormativeContent` | | Inverse of the above. |
| `directlyPrevailsOver` | object property ⊑ `prevailsOver` | `NormativeContent` → `NormativeContent` | A I | Superproperty of the asserted shortcuts. |
| `exceptionPrevailsOver` | object property ⊑ `prevailsOver` | `NormativeContent` → `NormativeContent` | | Typed edge for undercutting defeat. |
| `conflictPrevailsOver` | object property ⊑ `prevailsOver` | `NormativeContent` → `NormativeContent` | | Typed edge for rebutting defeat resolved by a principle. |
| `temporalPrevailsOver` | object property ⊑ `prevailsOver` | `NormativeContent` → `NormativeContent` | | Typed edge for repeal. |
| `isExceptionTo` | object property ⊑ `directlyPrevailsOver`, `exceptionPrevailsOver` | `NormativeContent` → `NormativeContent` | | Shortcut: the subject is a carve-out from the object, without a reified defeater. |
| `rankLevel` | datatype property | `NormativeRank` → `xsd:integer` | F | Integer ordinal making lex superior computable. |
| `ConstitutionalRank` | individual, `NormativeRank` | | | Level 40. Constitutional or founding instruments, including treaties that head the legal order. |
| `LegislativeRank` | individual, `NormativeRank` | | | Level 30. Primary legislation. |
| `RegulatoryRank` | individual, `NormativeRank` | | | Level 20. Secondary or implementing instruments. |
| `DelegatedRank` | individual, `NormativeRank` | | | Level 10. Delegated acts, technical annexes and equivalents. |
| `OrganisationalRank` | individual, `NormativeRank` | | | Level 0. Internal organisational instruments. |
| `Strict` | individual, `NormStrength` | | | Admits no defeat. |
| `Defeasible` | individual, `NormStrength` | | | May be withdrawn by an applicable defeater; the default. |
| `LexSuperior` | individual, `ResolutionPrinciple` | | | Precedence to the norm of higher rank. |
| `LexSpecialis` | individual, `ResolutionPrinciple` | | | Precedence to the more specific norm. |
| `LexPosterior` | individual, `ResolutionPrinciple` | | | Precedence to the later norm. |

### A.5 Counts-as chaining (2)

| Term | Kind | Domain → Range | Char. | Definition |
|---|---|---|---|---|
| `establishesTrigger` | object property | `NormativeContent` → `TriggerEvent` | | A trigger event that holds whenever the content applies: the institutional fact it brings about. |
| `isTriggerEstablishedBy` | object property | `TriggerEvent` → `NormativeContent` | | Inverse of the above. |

---

## Appendix B — catalogue of the `normad` module

Namespace `normad:` = `https://w3id.org/def/norma-o/deriv#`.

### B.1 Classes (7)

| Class | Superclass | Definition |
|---|---|---|
| `DerivationActivity` | `prov:Activity` | A run that materialises normative conclusions from an annotation graph. Must record at least one assumption. |
| `PrevalenceOrdering` | `prov:Entity` | A computed stratification of a defeat digraph, static or for one case. |
| `NormEvaluation` | `prov:Entity` | The outcome for one norm within one ordering: level, and per case status and reach. |
| `PrevalenceCycle` | `prov:Entity` | A cycle in a defeat digraph, reported rather than resolved. |
| `ApplicabilityStatus` | `skos:Concept` | Whether a norm applies to a case and, if not, why not. Scheme `ApplicabilityStatusScheme`. |
| `Assumption` | `skos:Concept` | A non-monotonic reading adopted by a derivation. Scheme `AssumptionScheme`. |
| `CycleKind` | `skos:Concept` | The legal reading of a cycle. Scheme `CycleKindScheme`. |

### B.2 Properties (16)

| Property | Kind | Domain → Range | Char. | Definition |
|---|---|---|---|---|
| `computedUnderAssumption` | object | `DerivationActivity` → `Assumption` | | An assumption the conclusions depend on. Inverse `isAssumptionOf`. |
| `isAssumptionOf` | object | `Assumption` → `DerivationActivity` | | Inverse of the above. |
| `forFactPattern` | object | `PrevalenceOrdering` → `norma:FactPattern` | F | The case an ordering was computed for. Absent on the static ordering. |
| `inOrdering` | object | `NormEvaluation` → `PrevalenceOrdering` | F | The ordering an evaluation belongs to. |
| `evaluatedNorm` | object | `NormEvaluation` → `norma:NormativeContent` | F | The norm evaluated. |
| `hasApplicabilityStatus` | object | `NormEvaluation` → `ApplicabilityStatus` | F | The outcome the case yields for the norm. |
| `reachesParty` | object | `NormEvaluation` → `norma:LegalParty` | | A concrete party the norm reaches in the case. |
| `inCycle` | object | `PrevalenceOrdering` → `PrevalenceCycle` | | A cycle found while computing the ordering. |
| `involvesNorm` | object | `PrevalenceCycle` → `norma:NormativeContent` | | A norm on the cycle. |
| `hasCycleKind` | object | `PrevalenceCycle` → `CycleKind` | F | The legal reading of the cycle. |
| `citesCompetingPrinciple` | object | `PrevalenceCycle` → `norma:ResolutionPrinciple` | | A principle cited by a conflict defeater on the cycle. |
| `ruleSetVersion` | datatype | `DerivationActivity` → `xsd:string` | F | Rule set and version applied. |
| `derivedGraph` | datatype | `DerivationActivity` → `xsd:anyURI` | F | Name of the graph the conclusions were written to. |
| `prevalenceLevel` | datatype | `NormEvaluation` → `xsd:nonNegativeInteger` | F | The rung of the ladder, on the condensation. |
| `stratumCount` | datatype | `PrevalenceOrdering` → `xsd:nonNegativeInteger` | F | Number of rungs. |
| `isAcyclic` | datatype | `PrevalenceOrdering` → `xsd:boolean` | F | Whether the defeat digraph is acyclic. |

### B.3 Individuals (16)

| Individual | Type | Meaning |
|---|---|---|
| `Invalid` | `ApplicabilityStatus` | Not a member of the normative system. |
| `NotActivated` | `ApplicabilityStatus` | Valid, but not triggered by the case. |
| `Applicable` | `ApplicabilityStatus` | Valid, activated and undefeated or reinstated. |
| `Defeated` | `ApplicabilityStatus` | Valid and activated, but withdrawn by an applicable norm. |
| `Undecided` | `ApplicabilityStatus` | The grounded fixpoint leaves it open. |
| `ClosedGraph` | `Assumption` | Absence from the graph means absence from the system. |
| `ClosedCaseDescription` | `Assumption` | Silence about a condition means it does not hold. |
| `DefeatConsidered` | `Assumption` | Defeat was taken into account. |
| `DefeatNotConsidered` | `Assumption` | Defeat was ignored. |
| `GroundedSemantics` | `Assumption` | Defeat evaluated under Dung's grounded semantics. |
| `ReinstatementNotComputed` | `Assumption` | Defeat applied one level deep. |
| `InstitutionalFactsChained` | `Assumption` | Facts established by applicable constitutive rules were fed back into the case. |
| `OpenCounterparty` | `Assumption` | An unnamed counterparty is read as not disagreeing. |
| `SecondDegreeConflict` | `CycleKind` | Conflict defeaters on the cycle cite different principles. |
| `AnnotationContradiction` | `CycleKind` | Conflict defeaters cite the same principle in opposite directions. |
| `IrresolubleAntinomy` | `CycleKind` | The defeat cites no principle. |
