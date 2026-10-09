# Voluntary Contribution Mechanism (VCM) in oTree

A linear public goods game with a structural break in the marginal per capita return (MPCR) and random re-matching of groups at the break.

## Design

Each subject *i* in a group of size *N* receives an endowment *E* and chooses a contribution *c<sub>i</sub>* ∈ {0, 1, …, *E*}. Earnings in a round are

π<sub>i</sub> = (E − c<sub>i</sub>) + α · Σ<sub>j</sub> c<sub>j</sub>

| Parameter | Value |
|---|---|
| Group size *N* | 3 |
| Endowment *E* | 20 points |
| Rounds | 10 |
| Phase 1 (rounds 1 to 5) | α = 0.4 |
| Phase 2 (rounds 6 to 10) | α = 0.8 |
| Matching | Random groups in round 1, fixed through round 5; randomly re-formed in round 6, fixed through round 10 |
| Payment | Sum of earnings over all rounds |

Both MPCR values satisfy 1/N < α < 1, so each phase is a social dilemma: full free riding is the dominant strategy for a payoff-maximizing subject, while full contribution maximizes group earnings.

At the break, groups are redrawn until the partition differs from phase 1, so that re-matching actually changes group composition. This requires at least two groups (six or more participants, in multiples of three).

All parameters are constants in `assign2/assign2/__init__.py` (class `C`).

## Screens

1. **Instructions** (round 1): rules, earnings formula, worked numerical example, and the full two-phase schedule, so subjects know in advance that the MPCR and groups will change.
2. **Phase 2 begins** (round 6): announces the new MPCR and the re-formed groups.
3. **Contribution decision** (every round): status bar (round, phase, MPCR, endowment, group size), earnings formula with the current MPCR, an earnings calculator, and a history of earlier rounds with the current group.
4. **Results** (every round): own and others' (anonymous) contributions, group total, and an itemized breakdown of earnings; a notice before the phase change.
5. **Summary** (round 10): table of all rounds and total earnings.

## Data

Per round: `subsession.phase`, `subsession.mpcr`, `group.total_contribution`, `group.individual_share`, `player.contribution`, `player.payoff`.

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r assign2/requirements.txt requests
cd assign2
otree devserver
```

Open http://localhost:8000 and start the session `vcm` (6 demo participants).

## Tests

```bash
cd assign2
otree test vcm 6
```

The bots check the MPCR schedule and the condition 1/N < α < 1, fixed groups within each phase, changed groups at the break, rejection of out-of-range contributions, the earnings formula in every round, and the total on the summary page.
