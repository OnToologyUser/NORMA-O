# NORMA-O: The NORMA Ontology for Legal Norm Annotations

[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.19765301-blue)](https://doi.org/10.5281/zenodo.19765301)
[![OWL 2 DL](https://img.shields.io/badge/Ontology-OWL%202%20DL-orange)](https://www.w3.org/TR/owl2-overview/)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Docs](https://img.shields.io/badge/Documentation-w3id.org%2Fdef%2Fnorma--o-navy)](https://w3id.org/def/norma-o)
[![Zenodo Community](https://img.shields.io/badge/Zenodo-NORMA%20Community-blue?logo=zenodo)](https://zenodo.org/communities/norma)

**NORMA-O** is an OWL 2 DL ontology for the formal semantic representation of machine-readable legal norm annotations. It provides a structured vocabulary for publishing, integrating, and reusing annotations derived from regulatory texts, while preserving full traceability to the legal source and accountability for the annotation process.

> **IRI:** `https://w3id.org/def/norma-o`  
> **Version IRI:** `https://w3id.org/def/norma-o/2.0` (current) · `https://w3id.org/def/norma-o/1.0` (prior)  
> **Preferred prefix:** `norma`  
> **Derivation module:** `https://w3id.org/def/norma-o/deriv` (prefix `normad`)  
> **Documentation:** [release 2.0](release/2.0.0/) · [WIDOCO HTML for 1.0](https://w3id.org/def/norma-o/1.0)

This ontology is the TBox component of the **NORMA Semantic Toolkit** — see [`sheyls/norma-semantic-toolkit`](https://github.com/sheyls/norma-semantic-toolkit) for the full toolkit including the BPMN annotation methodology, knowledge graph construction pipeline, SWRL rule engine, and REST API.

---

## What's new in 2.0

Version 2.0 keeps every term of 1.0 and adds the means to state how norms relate to each other and to concrete cases, and to compute what applies, to whom and why:

- **Standard Deontic Logic grounding** — action negation (`isNegationOf`), `Facultative`, `WeakPermission`, and deontic equivalence, contradiction and conflict between norms.
- **Hohfeldian legal positions** — `Duty`, `Claim`, `Privilege` and `NoRight`, with holder, counterparty, correlatives and jural opposites.
- **Roles, parties and cases** — `LegalRole`, `LegalParty`, `RoleAssignment`, `FactPattern`, and `confersRole` for constitutive rules.
- **Defeasibility** — `ExceptionDefeater`, `ConflictDefeater` and `TemporalDefeater`; lex superior, specialis and posterior; normative rank; norm strength; and a prevalence digraph.
- **Counts-as chaining** — `establishesTrigger` lets a constitutive rule establish an institutional fact that conditions regulative norms, so that defeating a classification (e.g. the high-risk classification of the AI Act) withdraws every obligation that depends on it.
- **Derivation module and reference rule set** — the `normad` module and [`deriv/`](release/2.0.0/deriv/) compute the deontic closure, positions, prevalence ordering with cycle detection, per-case applicability and weak permissions.

`norma:exception` is deprecated and `norma:UnderReview` moved to `ReviewStatus`. See [What's new in 2.0](release/2.0.0/WHATS-NEW.md) for the full description, migration guide, worked examples, term catalogue and known limitations.

---

## Table of Contents

- [What's new in 2.0](#whats-new-in-20)
- [Overview](#overview)
- [Methodology: LOT](#methodology-lot)
- [Competency Questions](#competency-questions)
- [Ontology Diagram](#ontology-diagram)
- [Scope](#scope)
- [Principal Classes](#principal-classes)
- [Statistics](#statistics)
- [Alignments](#alignments)
- [Downloads](#downloads)
- [Ontology Requirements Specification Document](#ontology-requirements-specification-document)
- [Citation](#citation)
- [License](#license)

---

## Overview

Regulatory requirements are increasingly expected to be machine-readable: traceable to their legal source, classifiable by type and binding force, and queryable in automated compliance pipelines. NORMA-O provides the semantic backbone for this, enabling legal knowledge engineers and developers to publish normative content as structured, interoperable knowledge graph resources.

The ontology models normative content together with the legal context needed to interpret it. It distinguishes between regulative norms (obligations, prohibitions, permissions, recommendations, negative recommendations) and constitutive rules (definitional or classificatory statements), and represents each legal element — agent, action, object, condition, source — as a distinct entity rather than a free-text blob.

Three design principles shape the model:

1. **Explicit conditional applicability** — a `norma:TriggerEvent` links a specific condition outcome to the normative content it activates, following the W3C n-ary relation pattern. This makes branch-sensitive activation queryable rather than buried in unstructured text.
2. **Reuse of established standards** — PROV-O for annotation provenance, ELI for legal resource references, FOAF for agent metadata, and SKOS for controlled classification values.
3. **First-class provenance** — the ontology records not only what a norm says, but who produced the annotation, by what method, and with what review status.

---

## Methodology: LOT

NORMA-O was developed following the **LOT (Linked Open Terms) methodology** for ontology engineering. LOT is an industrial ontology development process that provides a systematic workflow for building OWL ontologies aligned with Linked Data best practices.

| LOT Activity | Output in NORMA-O |
|---|---|
| Requirements specification | Competency questions (see below) |
| Conceptualisation | Conceptual model — classes, relations, controlled vocabularies |
| Implementation | OWL 2 DL axiomatisation in Turtle and RDF/XML |
| Publication | Persistent IRI (`w3id.org/def/norma-o`), WIDOCO HTML documentation, Zenodo release |
| Evaluation | SPARQL-based CQ evaluation against the EU AI Act ABox |

> **Reference:** Poveda-Villalón, M., Gómez-Pérez, A., & Suárez-Figueroa, M. C. (2022). LOT: An industrial oriented ontology engineering framework. *Engineering Applications of Artificial Intelligence*, 111, 104755. https://doi.org/10.1016/j.engappai.2022.104755

---

## Competency Questions

The following competency questions (CQs) guided the ontology design and serve as evaluation criteria. Each CQ can be answered by a SPARQL query over an ABox that instantiates NORMA-O.

| ID | Competency Question |
|---|---|
| CQ1 | What type of normative content does a given annotation represent — a regulative norm (obligation, prohibition, permission, recommendation, or negative recommendation) or a constitutive rule? |
| CQ2 | Under which conditions does a norm apply, and which specific condition outcome activates it? |
| CQ3 | Who is the legal agent bearing the obligation, right, or restriction stated by a norm? |
| CQ4 | What action is required, prohibited, or permitted under the norm? |
| CQ5 | What legal object does the regulated action concern? |
| CQ6 | From which legal source (regulation, directive, article, paragraph) does the norm derive? |
| CQ7 | Who produced the annotation, by which method (manual, automated, semi-automated), and under what review status? |
| CQ8 | What is the binding force (hard law, soft law) and compliance criticality (high, medium, low) of a norm? |
| CQ9 | What is the current lifecycle status of a norm (active, superseded, repealed)? |
| CQ10 | Which normative statements are activated when a given condition outcome holds? |

---

## Ontology Diagram

The diagram below shows the principal classes and object properties of NORMA-O 2.0. The 1.0 diagram is [here](release/1.0.0/norma-o.svg), and the derivation module's diagram [here](release/2.0.0/norma-o-deriv-v1.svg).

![NORMA-O ontology diagram](release/2.0.0/norma-o-v2.svg)

*Diagram generated with [diagrams.net](https://www.diagrams.net/).*

---

## Scope

The ontology covers the following aspects of legal norm annotations:

- **Regulative norms** — obligations, prohibitions, permissions, recommendations, and negative recommendations
- **Constitutive rules** — statements that define statuses, classifications, or institutional facts
- **Legal conditions and their evaluated outcomes** — including branch-sensitive activation via the `norma:TriggerEvent` n-ary relation pattern
- **Legal agents, actions, objects, and sources**
- **Provenance and annotation metadata** — extraction method, review status, lifecycle status, and source traceability

The ontology does not model procedural or institutional rules beyond what is necessary to contextualise normative content, nor does it encode substantive regulatory knowledge — that is the role of the ABox.

---

## Principal Classes

| Class | Description |
|---|---|
| `norma:NormativeContent` | Abstract superclass for all machine-readable legal content extracted from a legal source |
| `norma:RegulativeNorm` | A normative statement governing conduct |
| `norma:Obligation` | A regulative norm requiring an action |
| `norma:Prohibition` | A regulative norm forbidding an action |
| `norma:Permission` | A regulative norm allowing an action |
| `norma:Recommendation` | A regulative norm recommending an action (soft norm) |
| `norma:NegativeRecommendation` | A regulative norm advising against an action (soft norm) |
| `norma:ConstitutiveRule` | A statement that defines or qualifies a legal or institutional situation |
| `norma:LegalCondition` | A condition or criterion relevant to the applicability of a norm |
| `norma:ConditionOutcome` | An evaluated branch of a legal condition (e.g., true / false) |
| `norma:TriggerEvent` | Reification of the relation between a condition outcome and the norm it activates |
| `norma:LegalAgent` | An agent (person, organisation, or role) mentioned in a norm |
| `norma:LegalAction` | An action regulated by a norm |
| `norma:LegalObject` | An entity that is the object of the regulated action |
| `norma:LegalSource` | Work-level reference to a legal document (aligned with ELI) |
| `norma:LegalSourceExpression` | Expression-level reference to a specific version of a legal document |
| `norma:AnnotationActivity` | The activity that produced an annotation (aligned with PROV-O `Activity`) |
| `norma:AnnotatorAgent` | The agent responsible for an annotation activity |
| `norma:BindingForce` | SKOS concept class for binding force (hard law, soft law, …) |
| `norma:ComplianceCriticality` | SKOS concept class for criticality levels (high, medium, low) |
| `norma:NormStatus` | SKOS concept class for lifecycle status (active, superseded, repealed) |
| `norma:ReviewStatus` | SKOS concept class for review state (pending review, reviewed, …) |
| `norma:ExtractionMethod` | SKOS concept class for annotation method (manual, automated, semi-automated) |

---

## Statistics

| Element | 1.0 | 2.0 | `normad` module |
|---|---:|---:|---:|
| Classes | 23 | 41 | 7 |
| Object properties | 41 | 102 | 11 |
| Datatype properties | 24 | 25 | 5 |
| Named individuals (TBox controlled vocabulary) | 23 | 33 | 16 |
| OWL profile | OWL 2 DL | OWL 2 DL | OWL 2 DL |

The principal classes listed above are those of 1.0. The classes added in 2.0 are catalogued in [WHATS-NEW.md](release/2.0.0/WHATS-NEW.md#appendix-a--catalogue-of-new-core-terms).

---

## Alignments

NORMA-O imports and aligns with the following established vocabularies:

| Vocabulary | Alignment type | Role in NORMA-O |
|---|---|---|
| [PROV-O](http://www.w3.org/ns/prov#) | `owl:imports` | Provenance of annotation activities and annotator agents |
| [ELI](http://data.europa.eu/eli/ontology) | `owl:imports` | Work-level and expression-level references to legal sources |
| [FOAF](http://xmlns.com/foaf/0.1/) | `owl:imports` | Project metadata |
| [SKOS](http://www.w3.org/2004/02/skos/core#) | Structural reuse | Controlled vocabulary classes and concept schemes |
| [LKIF-Core](http://www.estrellaproject.org/lkif-core/) | Informative (`skos:closeMatch`, `skos:broadMatch`) | Semantic alignment with legal knowledge interchange format |

---

## Downloads

**Version 2.0 (current)**

| Format | File | Description |
|---|---|---|
| Turtle (preferred) | [`norma-ontology-v2.ttl`](release/2.0.0/norma-ontology-v2.ttl) | Core ontology, OWL 2 DL |
| RDF/XML | [`norma-ontology-v2.rdf`](release/2.0.0/norma-ontology-v2.rdf) | Equivalent serialisation in RDF/XML |
| Turtle / RDF/XML | [`norma-o-deriv.ttl`](release/2.0.0/norma-o-deriv.ttl) / [`.rdf`](release/2.0.0/norma-o-deriv.rdf) | `normad` derivation module |
| Python | [`deriv/`](release/2.0.0/deriv/) | Reference rule set and checks |

**Version 1.0**

| Format | File | Description |
|---|---|---|
| Turtle | [`norma-ontology-v1.ttl`](release/1.0.0/norma-ontology-v1.ttl) | Primary source file, OWL 2 DL |
| RDF/XML | [`norma-ontology-v1.rdf`](release/1.0.0/norma-ontology-v1.rdf) | Equivalent serialisation in RDF/XML |
| OWL/XML, JSON-LD, N-Triples | via [WIDOCO docs](https://w3id.org/def/norma-o/1.0) | Auto-generated |
| Ontology Requirements Specification Document (PDF) | [`ords.pdf`](release/1.0.0/ords.pdf) | Requirements specification document |

Content negotiation is supported at `https://w3id.org/def/norma-o` (latest, currently 2.0), at the version IRIs `/2.0` and `/1.0`, and at `https://w3id.org/def/norma-o/deriv`:

```bash
# Turtle
curl -L -H "Accept: text/turtle" https://w3id.org/def/norma-o

# RDF/XML
curl -L -H "Accept: application/rdf+xml" https://w3id.org/def/norma-o
```

For 2.0, browsers are redirected to the [release folder](release/2.0.0/), and JSON-LD or N-Triples requests fall back to RDF/XML.

---

## Ontology Requirements Specification Document

The ontology requirements specification document is available as PDF here: [`ords.pdf`](release/1.0.0/ords.pdf).

<a href="release/1.0.0/ords.pdf">
  <img src="release/1.0.0/ords-preview.png" alt="Ontology Requirements Specification Document preview" width="720">
</a>

*Click the preview image to open the full PDF.*

---

## Citation

If you use NORMA-O in your research, please cite the version you used. For version 2.0:

```bibtex
@misc{leyvaSanchez2026normaO,
  title        = {{NORMA-O}: The {NORMA} Ontology for Legal Norm Annotations},
  author       = {Leyva-Sánchez, Sheyla and Poveda-Villalón, María and Rodríguez-Doncel, Víctor},
  year         = {2026},
  version      = {2.0},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.24116269},
  url          = {https://doi.org/10.5281/zenodo.24116269}
}
```

| Version | DOI |
|---|---|
| 2.0 | [10.5281/zenodo.24116269](https://doi.org/10.5281/zenodo.24116269) |
| 1.0 | [10.5281/zenodo.19765302](https://doi.org/10.5281/zenodo.19765302) |
| All versions (always resolves to the latest) | [10.5281/zenodo.19765301](https://doi.org/10.5281/zenodo.19765301) |

---

## License

This ontology is released under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) licence.

Copyright © 2026 Sheyla Leyva-Sánchez and contributors. Ontology Engineering Group, Universidad Politécnica de Madrid.

You are free to share and adapt this material for any purpose, including commercially, as long as you give appropriate credit, provide a link to the licence, and indicate if changes were made.

---

## Part of the NORMA Ecosystem

NORMA-O is the TBox component of a broader open resource for legal knowledge engineering:

| Resource | Description |
|---|---|
| [`sheyls/NORMA-O`](https://github.com/sheyls/NORMA-O) | This repository — ontology TBox only |
| [`sheyls/norma-semantic-toolkit`](https://github.com/sheyls/norma-semantic-toolkit) | Full toolkit: annotation methodology, KG construction pipeline, SWRL engine, REST API, web app |
| [WIDOCO documentation (1.0)](https://w3id.org/def/norma-o/1.0) | Full HTML documentation with cross-reference of all 1.0 terms |
| [Zenodo community](https://zenodo.org/communities/norma) | All releases and supplementary materials |
