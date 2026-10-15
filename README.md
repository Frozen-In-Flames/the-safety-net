# the-safety-net

Welfare core for a new nation. Step 6 of the Nation Kit's 17-to-1
reverse-SDG build sequence. The final step.

## The idea

Every federal agency is one class with one job. This build centralizes
the three welfare classes:

- `Benefits`: one job: payments go out on time. A benefits ledger
  with pseudonymous beneficiary records (id, program, amount,
  schedule). Payment runs mark every due payment paid with a
  timestamp, and the on-time rate readout shows the share of due
  payments paid inside their window.
- `Disaster`: one job: show up with resources when it hits. A
  resource inventory (depot, resource type, quantity) plus incident
  records (type, locality, severity, status). The dispatch coordinator
  allocates depot stock to open incidents and reports unmet need in
  planning units.
- `Diplomacy`: one job: talk before fighting. A treaty and
  communications log (counterparty, type, date, status, summary) with
  an upcoming-obligations readout keyed on review dates, so no
  commitment slips quietly.

## SDGs unlocked

This build unlocks **SDG 1 (No Poverty)**, **SDG 2 (Zero Hunger)**,
**SDG 3 (Good Health and Well-Being)**, **SDG 4 (Quality Education)**,
**SDG 5 (Gender Equality)**, **SDG 6 (Clean Water and Sanitation)**,
**SDG 8 (Decent Work and Economic Growth)**, and **SDG 10 (Reduced
Inequalities)**:

- `Benefits` maps to 1: on-time payments keep beneficiaries out of
  destitution. It maps to 10: uniform benefit rules, paid identically
  regardless of who you are, narrow gaps instead of widening them. It
  maps to 8: an income floor lets people take decent work without
  desperation. It maps to 5: benefits paid on identical terms are
  gender-blind by construction.
- `Disaster` maps to 2: emergency food and water when harvests or
  supply lines fail. It maps to 3: medical stock and disease
  prevention in the aftermath. It maps to 6: emergency potable water
  when systems break. It maps back to 1: fast disaster response stops
  a shock from becoming permanent poverty.
- `Diplomacy` maps to 4: exchange and cooperation agreements carry
  knowledge and education across borders. It maps to 8: economic
  cooperation treaties underpin decent work. And honestly, its one job
  protects all eight: a war undoes every one of these goals, so the
  class that keeps nations talking is the shield around the rest.

It is step 6, the final step, because these goals are outcomes, not
inputs. On-time benefits require honest books (step 1, the-ledger).
Disaster coordination requires livable land and clean water (step 3,
the-shield) plus reachable addresses and working power (step 5,
the-commons). Diplomacy worth having requires a defended border behind
it (step 4, the-sword). Poverty is the last thing that falls, not the
first lever pulled. That is the whole thesis of the 17-to-1 sequence:
the UN's goals are the right set in the wrong order, and this build
order puts the prerequisites first.

## Usage

```bash
# Benefits: enroll, run payments, read the on-time rate
python3 safety_net_cli.py benefits enroll --id BEN-001 --program retirement --amount 1200 --schedule monthly
python3 safety_net_cli.py benefits enroll --id BEN-002 --program disability --amount 900 --schedule monthly
python3 safety_net_cli.py benefits run
python3 safety_net_cli.py benefits on-time --days 90
python3 safety_net_cli.py benefits summary

# Disaster: stock depots, report an incident, dispatch, check unmet need
python3 safety_net_cli.py disaster stock --depot north --resource water --quantity 10000
python3 safety_net_cli.py disaster stock --depot north --resource food --quantity 10000
python3 safety_net_cli.py disaster report --type flood --locality Riverside --severity 2
python3 safety_net_cli.py disaster dispatch --incident INC-0001
python3 safety_net_cli.py disaster unmet --incident INC-0001
python3 safety_net_cli.py disaster resolve --incident INC-0001

# Diplomacy: log entries, watch upcoming obligations
python3 safety_net_cli.py diplomacy log --counterparty Atlantis --type treaty --date 2026-01-15 --summary "Mutual recognition and trade" --review-date 2027-01-15
python3 safety_net_cli.py diplomacy obligations --within-days 90
python3 safety_net_cli.py diplomacy summary
```

Data persists as JSON under `data/` (override with `--data-dir`).
See `demo/sample-output.md` for a full end-to-end run.

## Honest limits

- These are ledgers, not operations. `Benefits` tracks payments; it
  does not fund programs or move money. `Disaster` coordinates stock
  on the books; it does not drive trucks, own warehouses, or rescue
  anyone. `Diplomacy` keeps the conversation logged; it does not
  negotiate.
- Beneficiary ids are pseudonymous by design. Real identity
  management is a separate, harder job this build does not attempt.
- Disaster need is estimated from a severity table in planning units.
  It is triage math, labeled as such, never a promise of what will
  arrive.
- On-time rate measures the ledger's own discipline, not whether the
  amounts are adequate. A nation can pay 100% on time and still pay
  too little. That is a policy question, not a software question.
- Demo figures are sample data. Every real figure this tool reports
  carries its source and date.

## TRL

TRL 8: system complete and qualified. 48/48 tests green with no
network access in the test suite, CLI demonstrated end-to-end, v0.1.0
released. The gap to 9 is operational use: real caseworkers running
real payment runs, real dispatchers coordinating real stock, real
diplomats keeping a real log.

## License

Apache-2.0.
