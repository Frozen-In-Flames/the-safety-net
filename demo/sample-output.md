# the-safety-net: end-to-end demo

Sample run, generated 2026-10-15 with demo data. All figures below are sample data, not real benefits, stock, or treaties.

```
### 1. Enroll beneficiaries
{
  "id": "BEN-001",
  "program": "retirement",
  "amount": 1200.0,
  "schedule": "monthly",
  "enrolled_at": "2026-10-15T20:10:40.651807+00:00",
  "source": "nation benefits ledger"
}
{
  "id": "BEN-002",
  "program": "disability",
  "amount": 900.0,
  "schedule": "monthly",
  "enrolled_at": "2026-10-15T20:10:40.707535+00:00",
  "source": "nation benefits ledger"
}
{
  "id": "BEN-003",
  "program": "survivor",
  "amount": 750.0,
  "schedule": "biweekly",
  "enrolled_at": "2026-10-15T20:10:40.813094+00:00",
  "source": "nation benefits ledger"
}

### 2. Run payments (nothing due yet: enrollment is today)
paid 0 payment(s)
[]

### 3. Ledger summary
{
  "beneficiaries": 3,
  "by_program": {
    "retirement": 1,
    "disability": 1,
    "survivor": 1
  },
  "payments_made": 0,
  "total_paid": 0,
  "on_time_rate_90_days": null,
  "due_in_window": 0,
  "on_time_in_window": 0,
  "source": "nation benefits ledger",
  "as_of": "2026-10-15T20:10:40.931617+00:00"
}

### 4. Stock disaster depots
{
  "depot": "north",
  "resource": "water",
  "quantity": 10000.0
}
{
  "depot": "north",
  "resource": "food",
  "quantity": 10000.0
}
{
  "depot": "north",
  "resource": "blankets",
  "quantity": 5000.0
}
{
  "depot": "south",
  "resource": "medical",
  "quantity": 2000.0
}

### 5. Report a severity-3 flood, dispatch, check unmet need
{
  "id": "INC-0001",
  "type": "flood",
  "locality": "Riverside",
  "severity": 3,
  "status": "open",
  "reported_at": "2026-10-15T20:10:41.267847+00:00",
  "source": "nation disaster registry"
}
dispatched to INC-0001 (Riverside): 4 resource line(s), unmet: 500 shelter_kits
{
  "incident": "INC-0001",
  "locality": "Riverside",
  "dispatched_at": "2026-10-15T20:10:41.318681+00:00",
  "allocations": {
    "blankets": 1000,
    "food": 2000,
    "medical": 100,
    "water": 2000
  },
  "unmet": {
    "shelter_kits": 500
  },
  "note": "planning units from severity table, not promises",
  "source": "nation disaster registry"
}

### 6. Log diplomacy, read upcoming obligations
{
  "id": "DIP-0001",
  "counterparty": "Atlantis",
  "type": "treaty",
  "date": "2026-01-15",
  "status": "active",
  "summary": "Mutual recognition and trade",
  "review_date": "2027-01-15",
  "logged_at": "2026-10-15T20:10:41.372916+00:00",
  "source": "nation diplomacy log"
}
{
  "id": "DIP-0002",
  "counterparty": "Pacifica",
  "type": "summit",
  "date": "2026-06-01",
  "status": "active",
  "summary": "Regional disaster-response coordination",
  "review_date": null,
  "logged_at": "2026-10-15T20:10:41.427328+00:00",
  "source": "nation diplomacy log"
}
1 obligation(s) within 365 days
[
  {
    "id": "DIP-0001",
    "counterparty": "Atlantis",
    "type": "treaty",
    "date": "2026-01-15",
    "status": "active",
    "summary": "Mutual recognition and trade",
    "review_date": "2027-01-15",
    "logged_at": "2026-10-15T20:10:41.372916+00:00",
    "source": "nation diplomacy log",
    "days_until_review": 92,
    "overdue": false
  }
]
```
