# Drug graveyard x human genetics — first pass (2026-10-31)

Pipeline: ClinicalTrials.gov terminated industry Phase 2/3 drug trials (5,490) -> stopped for business reasons, not safety/efficacy (878)
-> Open Targets: never-approved, no drug warnings (223 drugs) -> each target's diseases with genetic_association >= 0.6, excluding old indications
-> 850 drug-disease pairs across 82 drugs (`matches.csv`).

Raw scores are direction-blind (e.g. CTLA4 blockers -> autoimmunity is backwards). Hand pass for direction of effect:

## Validation (method rediscovers real therapies)
- CXCR4 antagonist (ulocuplumab) -> WHIM syndrome (CXCR4 gain-of-function). Mavorixafor, another CXCR4 antagonist, was FDA-approved for WHIM in 2024.
- MEK1 inhibitor (WX-554) -> RASopathy / CFC syndrome (MEK gain-of-function). MEK inhibitors are already used off-label in RASopathy cardiomyopathy.

## Direction-consistent candidates to check
| Shelved drug | Stage | Mechanism | Why stopped | New disease (genetic score) | Direction logic |
|---|---|---|---|---|---|
| Rapastinel | Ph3 | NMDA partial agonist | business decision (MDD) | GRIN1/2 loss-of-function neurodevelopmental disorders (0.97) | boost hypofunctional NMDA receptors; only LoF patients |
| Miransertib | Ph2 | AKT inhibitor | business reasons (PROS) | MPPH megalencephaly, AKT3 gain-of-function (0.87) | inhibit overactive AKT3 |
| Sapanisertib | Ph2 | mTOR inhibitor | funding | focal cortical dysplasia II, mTOR gain-of-function (0.93) | inhibit overactive mTOR (rapalogs already used in TSC) |
| Lixivaptan | Ph3 | V2 receptor antagonist | reassessment (ADPKD) | nephrogenic SIAD, AVPR2 gain-of-function (0.85) | block constitutively active V2R; some mutations vaptan-resistant; check liver signal |
| Cofirasersen | Ph2 | ENaC antisense | business decision | Liddle syndrome, ENaC gain-of-function (0.89) | correct direction, but amiloride is cheap: low value |
| Bemarituzumab | Ph3 | FGFR2b antibody | sponsor decision | Crouzon/Pfeiffer, FGFR2 gain-of-function (0.95) | isoform mismatch (IIIb vs IIIc) likely kills it |

Rejected for wrong direction (examples): danicamtiv -> HCM, BMS-754807 -> Donohue, mocetinostat -> Cornelia de Lange, CTLA4/CD40 drugs -> autoimmunity.

## Next
1. Automate direction of effect (Open Targets evidence directionOnTrait / variant LoF vs GoF) so the hand pass scales to all 850.
2. For each survivor: who holds the asset now, patent life, existing literature (is it already being tried?), patient numbers.
3. Pick one asset and write a 2-page repurposing case; test with a rare-disease foundation or the asset holder.

## Direction automation: negative result (2026-10-31)
direction.py tags each pair using Open Targets directionOnTarget/directionOnTrait. It FAILS validation:
WHIM, MPPH, FCD II and Liddle (all gain-of-function, need an inhibitor) come out as "need up", because eva (ClinVar) and impc (mouse knockouts)
label almost everything LoF. Only orphanet GoF tags are informative, and they are sparse. Conclusion: direction for rare disease needs
per-pair literature curation. That curation is the real moat; the join itself is easy.

## Deep dive 1: rapastinel -> GRIN loss-of-function disorders
- Gap: GRIN gain-of-function has a company (GRIN Therapeutics, radiprodil NAM, FDA Breakthrough, pivotal Ph3 started Europe May 2026).
  Loss-of-function has only supplements (L-serine trials, spermidine case reports). No drug that boosts NMDA receptors is in trials.
- Rapastinel enhances NMDA receptor function, Phase 3 human safety (IV). Caveats to verify:
  * Allergan's 2019 Ph3 MDD trials missed efficacy, so "business decision" on the registry hides an efficacy miss in MDD (not safety).
  * Who holds it now (AbbVie via Allergan?), and whether the oral follow-on zelquistinel (Gate Neurosciences?) is the better asset.
  * Does it potentiate the specific LoF variants? Needs in-vitro test on mutant receptors (oocyte/HEK patch clamp; academic GRIN labs do this).
  * Only LoF patients qualify; GoF patients would be harmed. Variant function must be known per patient.
- Buyers/partners: GRIN patient foundations (CureGRIN, GRIN2B Foundation), asset holder, academic GRIN labs.
