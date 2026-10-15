"""the-safety-net: Benefits class.

SSA's one job: payments go out on time. Beneficiary records are
pseudonymous (id, program, amount, schedule); payment runs mark due
payments paid with timestamps; the on-time rate readout shows the share
of due payments paid inside their window. It tracks payments on the
books; it does not fund programs or move money. Funding is the
Treasury's job (the-ledger, step 1 of the Nation Kit).
"""

import datetime
import json
import os

SOURCE_LABEL = "nation benefits ledger"

PROGRAMS = ("retirement", "disability", "survivor", "child", "other")
SCHEDULES = ("monthly", "biweekly", "weekly")
SCHEDULE_DAYS = {"monthly": 30, "biweekly": 14, "weekly": 7}
# A payment counts as on time when run within this many days after due.
GRACE_DAYS = 3


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _parse(ts):
    return datetime.datetime.fromisoformat(ts)


class Benefits:
    """Benefits ledger: beneficiaries, payment runs, on-time rate."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._bpath = os.path.join(data_dir, "beneficiaries.json")
        self._ppath = os.path.join(data_dir, "payments.json")
        self._load()

    # -- persistence ----------------------------------------------------
    def _load(self):
        self._beneficiaries = {}
        self._payments = []
        if os.path.exists(self._bpath):
            with open(self._bpath) as f:
                self._beneficiaries = json.load(f)
        if os.path.exists(self._ppath):
            with open(self._ppath) as f:
                self._payments = json.load(f)

    def _save(self):
        with open(self._bpath, "w") as f:
            json.dump(self._beneficiaries, f, indent=2)
        with open(self._ppath, "w") as f:
            json.dump(self._payments, f, indent=2)

    # -- beneficiaries --------------------------------------------------
    def enroll(self, bid, program, amount, schedule):
        """Enroll a beneficiary. bid is a pseudonymous id, not a name."""
        if program not in PROGRAMS:
            raise ValueError("program must be one of %s" % (PROGRAMS,))
        if schedule not in SCHEDULES:
            raise ValueError("schedule must be one of %s" % (SCHEDULES,))
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("amount must be a positive number")
        if bid in self._beneficiaries:
            raise ValueError("beneficiary %s already enrolled" % bid)
        rec = {"id": bid, "program": program, "amount": float(amount),
               "schedule": schedule, "enrolled_at": _utcnow(),
               "source": SOURCE_LABEL}
        self._beneficiaries[bid] = rec
        self._save()
        return rec

    def beneficiary(self, bid):
        return self._beneficiaries.get(bid)

    def beneficiaries(self, program=None):
        recs = list(self._beneficiaries.values())
        if program is not None:
            recs = [r for r in recs if r["program"] == program]
        return sorted(recs, key=lambda r: r["id"])

    # -- payment runs ---------------------------------------------------
    def _last_paid_at(self, bid):
        paid = [p for p in self._payments
                if p["beneficiary"] == bid and p["status"] == "paid"]
        if not paid:
            return None
        return max(_parse(p["paid_at"]) for p in paid)

    def due_beneficiaries(self, at=None):
        """Beneficiaries with a payment due at or before `at` (default now)."""
        now = _parse(at) if at else datetime.datetime.now(
            datetime.timezone.utc)
        due = []
        for bid, rec in self._beneficiaries.items():
            last = self._last_paid_at(bid)
            anchor = last if last else _parse(rec["enrolled_at"])
            due_date = anchor + datetime.timedelta(
                days=SCHEDULE_DAYS[rec["schedule"]])
            if now >= due_date:
                due.append((bid, due_date))
        return sorted(due, key=lambda d: d[1])

    def run_payments(self, at=None):
        """Pay every due beneficiary. Returns the payment records created."""
        now = _parse(at) if at else datetime.datetime.now(
            datetime.timezone.utc)
        made = []
        for bid, due_date in self.due_beneficiaries(at=at):
            rec = self._beneficiaries[bid]
            late_days = (now - due_date).days
            on_time = late_days <= GRACE_DAYS
            pay = {"beneficiary": bid, "program": rec["program"],
                   "amount": rec["amount"], "schedule": rec["schedule"],
                   "due_date": due_date.isoformat(),
                   "paid_at": now.isoformat(), "status": "paid",
                   "on_time": on_time, "late_days": max(late_days, 0),
                   "source": SOURCE_LABEL}
            self._payments.append(pay)
            made.append(pay)
        self._save()
        return made

    def payments(self, bid=None):
        pays = list(self._payments)
        if bid is not None:
            pays = [p for p in pays if p["beneficiary"] == bid]
        return sorted(pays, key=lambda p: p["paid_at"])

    # -- readout --------------------------------------------------------
    def on_time_rate(self, days=90, at=None):
        """Share of payments due in the last `days` paid inside the window.

        Returns (rate, due_count, on_time_count). rate is None when no
        payments were due in the window.
        """
        now = _parse(at) if at else datetime.datetime.now(
            datetime.timezone.utc)
        cutoff = now - datetime.timedelta(days=days)
        window = [p for p in self._payments
                  if _parse(p["due_date"]) >= cutoff]
        if not window:
            return None, 0, 0
        on_time = sum(1 for p in window if p["on_time"])
        return on_time / len(window), len(window), on_time

    def summary(self, days=90):
        """Ledger health: enrollment, payout totals, on-time rate."""
        rate, due_n, on_n = self.on_time_rate(days=days)
        total_paid = sum(p["amount"] for p in self._payments
                         if p["status"] == "paid")
        by_program = {}
        for rec in self._beneficiaries.values():
            by_program[rec["program"]] = by_program.get(rec["program"], 0) + 1
        return {"beneficiaries": len(self._beneficiaries),
                "by_program": by_program,
                "payments_made": len(self._payments),
                "total_paid": round(total_paid, 2),
                "on_time_rate_%d_days" % days:
                    None if rate is None else round(100 * rate, 1),
                "due_in_window": due_n, "on_time_in_window": on_n,
                "source": SOURCE_LABEL, "as_of": _utcnow()}
