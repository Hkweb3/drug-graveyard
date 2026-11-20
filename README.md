# Drug Graveyard

Bring shelved drugs back to life for rare diseases.

Thousands of Phase 2/3 drugs are abandoned for **business** reasons, not safety. They have already been tested in humans. This project matches each one to rare diseases where **human genetics** says the drug's target is the cause.

## Pipeline

| Step | Script | Output |
|---|---|---|
| 1. Harvest | `pull_shelved.py`: terminated industry Phase 2/3 drug trials from ClinicalTrials.gov, keeping only those stopped for business reasons | 5,490 trials -> 878 business-stopped (`shelved.csv`) |
| 2. Match | `match.py`: never-approved drugs without safety warnings x Open Targets genetic associations (score >= 0.6), old indications excluded | 223 drugs -> 850 drug-disease pairs across 82 drugs (`matches.csv`) |
| 3. Direction | `direction.py`: does the drug push its target the way the disease needs? | `directed.csv` (first automated pass) |

Results and hand-checked leads are in [`FINDINGS.md`](FINDINGS.md).

## Validation

Without being told, the method rediscovers **CXCR4 antagonist -> WHIM syndrome** (mavorixafor, FDA-approved 2024) and **MEK inhibitor -> RASopathy**. Every change to the pipeline must still find these.

## Honest status

- Steps 1-2 work.
- Step 3's automated direction labels **failed validation** (genetic-evidence sources tag almost everything as loss-of-function). Direction has to be settled by reading the literature: extract claims, rank the evidence (human receptor electrophysiology > cell assays > animal data > reviews), check the effect at the clinical dose, and use two independent readers. That reading is the bottleneck.
- Top lead so far: **rapastinel -> GRIN loss-of-function disorders**. The case was sent to a patient foundation and to the current holder of the drug.

## Run

Python 3, standard library only. Each script calls public APIs (ClinicalTrials.gov v2, Open Targets GraphQL) and caches responses locally (`cache*.json`, git-ignored).

```
python pull_shelved.py
python match.py
python direction.py
```

Research prototype. Not medical advice.
