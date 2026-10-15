"""the-safety-net: Diplomacy class.

State's one job: talk before fighting. A log of counterparty records
(type treaty/notice/summit/communique, date, status, summary) with an
upcoming-obligations readout keyed on review dates. It keeps the
conversation on the books; it does not negotiate. Negotiation is the
diplomats' job.
"""

import datetime
import json
import os

SOURCE_LABEL = "nation diplomacy log"

ENTRY_TYPES = ("treaty", "notice", "summit", "communique")
ENTRY_STATUSES = ("active", "pending", "expired", "withdrawn")


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _today():
    return datetime.datetime.now(datetime.timezone.utc).date()


class Diplomacy:
    """Treaty and communications log with upcoming obligations."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._epath = os.path.join(data_dir, "diplomacy.json")
        self._load()

    # -- persistence ----------------------------------------------------
    def _load(self):
        self._entries = []
        if os.path.exists(self._epath):
            with open(self._epath) as f:
                self._entries = json.load(f)

    def _save(self):
        with open(self._epath, "w") as f:
            json.dump(self._entries, f, indent=2)

    # -- log ------------------------------------------------------------
    def log(self, counterparty, etype, date, summary, status="active",
            review_date=None):
        """Record a diplomatic entry. date and review_date are YYYY-MM-DD."""
        if etype not in ENTRY_TYPES:
            raise ValueError("type must be one of %s" % (ENTRY_TYPES,))
        if status not in ENTRY_STATUSES:
            raise ValueError("status must be one of %s" % (ENTRY_STATUSES,))
        try:
            datetime.date.fromisoformat(date)
        except ValueError:
            raise ValueError("date must be YYYY-MM-DD")
        if review_date is not None:
            try:
                datetime.date.fromisoformat(review_date)
            except ValueError:
                raise ValueError("review_date must be YYYY-MM-DD")
        entry = {"id": "DIP-%04d" % (len(self._entries) + 1),
                 "counterparty": counterparty, "type": etype, "date": date,
                 "status": status, "summary": summary,
                 "review_date": review_date, "logged_at": _utcnow(),
                 "source": SOURCE_LABEL}
        self._entries.append(entry)
        self._save()
        return entry

    def entries(self, counterparty=None, status=None, etype=None):
        out = list(self._entries)
        if counterparty is not None:
            out = [e for e in out if e["counterparty"] == counterparty]
        if status is not None:
            out = [e for e in out if e["status"] == status]
        if etype is not None:
            out = [e for e in out if e["type"] == etype]
        return sorted(out, key=lambda e: e["id"])

    def set_status(self, eid, status):
        if status not in ENTRY_STATUSES:
            raise ValueError("status must be one of %s" % (ENTRY_STATUSES,))
        for e in self._entries:
            if e["id"] == eid:
                e["status"] = status
                self._save()
                return e
        raise ValueError("unknown entry %s" % eid)

    # -- obligations ----------------------------------------------------
    def obligations(self, within_days=90):
        """Active or pending entries with a review date inside the window,
        soonest first. Overdue reviews are included and flagged."""
        today = _today()
        out = []
        for e in self._entries:
            if e["status"] not in ("active", "pending"):
                continue
            if not e["review_date"]:
                continue
            rd = datetime.date.fromisoformat(e["review_date"])
            delta = (rd - today).days
            if delta <= within_days:
                rec = dict(e)
                rec["days_until_review"] = delta
                rec["overdue"] = delta < 0
                out.append(rec)
        return sorted(out, key=lambda e: e["review_date"])

    def summary(self):
        by_status = {}
        by_type = {}
        for e in self._entries:
            by_status[e["status"]] = by_status.get(e["status"], 0) + 1
            by_type[e["type"]] = by_type.get(e["type"], 0) + 1
        parties = sorted({e["counterparty"] for e in self._entries})
        return {"entries": len(self._entries), "by_status": by_status,
                "by_type": by_type, "counterparties": parties,
                "upcoming_obligations_90d":
                    len(self.obligations(within_days=90)),
                "source": SOURCE_LABEL, "as_of": _utcnow()}
