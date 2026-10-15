"""the-safety-net: Disaster class.

FEMA's one job: show up with resources when it hits. Resource inventory
records what sits in which depot; incident records track type, locality,
severity, and status; the dispatch coordinator allocates depot stock to
open incidents and reports unmet need. It coordinates stock on the
books; it does not drive trucks or own warehouses. Logistics is a
separate job.
"""

import datetime
import json
import os

SOURCE_LABEL = "nation disaster registry"

SEVERITIES = (1, 2, 3, 4, 5)
STATUSES = ("open", "responding", "resolved")
INCIDENT_TYPES = ("flood", "fire", "storm", "earthquake", "drought",
                  "pandemic", "other")
RESOURCE_TYPES = ("water", "food", "shelter_kits", "medical", "generators",
                  "blankets", "fuel", "other")

# Planning units of each resource a severity level is estimated to need.
# Estimates for triage math, labeled as such, never promises.
SEVERITY_NEED = {
    1: {"water": 100, "food": 100},
    2: {"water": 500, "food": 500, "blankets": 200},
    3: {"water": 2000, "food": 2000, "shelter_kits": 500, "medical": 100,
        "blankets": 1000},
    4: {"water": 10000, "food": 10000, "shelter_kits": 2000, "medical": 500,
        "generators": 50, "blankets": 5000},
    5: {"water": 50000, "food": 50000, "shelter_kits": 10000,
        "medical": 2000, "generators": 200, "blankets": 20000},
}


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Disaster:
    """Resource inventory, incident records, dispatch coordinator."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._rpath = os.path.join(data_dir, "resources.json")
        self._ipath = os.path.join(data_dir, "incidents.json")
        self._dpath = os.path.join(data_dir, "dispatches.json")
        self._load()

    # -- persistence ----------------------------------------------------
    def _load(self):
        self._resources = {}
        self._incidents = {}
        self._dispatches = []
        for path, attr, default in ((self._rpath, "_resources", {}),
                                    (self._ipath, "_incidents", {}),
                                    (self._dpath, "_dispatches", [])):
            if os.path.exists(path):
                with open(path) as f:
                    setattr(self, attr, json.load(f))
            else:
                setattr(self, attr, default)

    def _save(self):
        with open(self._rpath, "w") as f:
            json.dump(self._resources, f, indent=2)
        with open(self._ipath, "w") as f:
            json.dump(self._incidents, f, indent=2)
        with open(self._dpath, "w") as f:
            json.dump(self._dispatches, f, indent=2)

    # -- inventory ------------------------------------------------------
    def stock(self, depot, resource, quantity):
        """Add quantity of a resource to a depot's inventory."""
        if resource not in RESOURCE_TYPES:
            raise ValueError("resource must be one of %s" % (RESOURCE_TYPES,))
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            raise ValueError("quantity must be a positive number")
        key = "%s|%s" % (depot, resource)
        self._resources[key] = self._resources.get(key, 0) + quantity
        self._save()
        return {"depot": depot, "resource": resource,
                "quantity": self._resources[key]}

    def inventory(self, depot=None):
        out = []
        for key, qty in sorted(self._resources.items()):
            d, r = key.split("|", 1)
            if depot is not None and d != depot:
                continue
            out.append({"depot": d, "resource": r, "quantity": qty})
        return out

    # -- incidents ------------------------------------------------------
    def report_incident(self, itype, locality, severity):
        """Open an incident record. Returns the record (id like INC-0001)."""
        if itype not in INCIDENT_TYPES:
            raise ValueError("type must be one of %s" % (INCIDENT_TYPES,))
        if severity not in SEVERITIES:
            raise ValueError("severity must be 1-5")
        iid = "INC-%04d" % (len(self._incidents) + 1)
        rec = {"id": iid, "type": itype, "locality": locality,
               "severity": severity, "status": "open",
               "reported_at": _utcnow(), "source": SOURCE_LABEL}
        self._incidents[iid] = rec
        self._save()
        return rec

    def incident(self, iid):
        return self._incidents.get(iid)

    def incidents(self, status=None):
        recs = list(self._incidents.values())
        if status is not None:
            if status not in STATUSES:
                raise ValueError("status must be one of %s" % (STATUSES,))
            recs = [r for r in recs if r["status"] == status]
        return sorted(recs, key=lambda r: r["id"])

    def resolve(self, iid):
        rec = self._incidents.get(iid)
        if rec is None:
            raise ValueError("unknown incident %s" % iid)
        rec["status"] = "resolved"
        self._save()
        return rec

    # -- dispatch -------------------------------------------------------
    def need(self, iid):
        """Estimated resource need for an incident (planning units)."""
        rec = self._incidents.get(iid)
        if rec is None:
            raise ValueError("unknown incident %s" % iid)
        return dict(SEVERITY_NEED[rec["severity"]])

    def _allocated(self, iid):
        alloc = {}
        for d in self._dispatches:
            if d["incident"] == iid:
                for r, q in d["allocations"].items():
                    alloc[r] = alloc.get(r, 0) + q
        return alloc

    def unmet_need(self, iid):
        """Need minus everything already dispatched to the incident."""
        need = self.need(iid)
        alloc = self._allocated(iid)
        return {r: q - alloc.get(r, 0) for r, q in need.items()
                if q - alloc.get(r, 0) > 0}

    def dispatch(self, iid):
        """Allocate depot stock to an open incident, first-fit by depot.

        Decrements inventory, marks the incident responding, and records
        what was allocated plus what remains unmet. Returns the dispatch
        record.
        """
        rec = self._incidents.get(iid)
        if rec is None:
            raise ValueError("unknown incident %s" % iid)
        if rec["status"] == "resolved":
            raise ValueError("incident %s is resolved" % iid)
        unmet = self.unmet_need(iid)
        allocations = {}
        # Deterministic depot order so runs are reproducible.
        for resource in sorted(unmet):
            want = unmet[resource]
            for key in sorted(self._resources):
                if want <= 0:
                    break
                depot, rtype = key.split("|", 1)
                if rtype != resource or self._resources[key] <= 0:
                    continue
                give = min(want, self._resources[key])
                self._resources[key] -= give
                want -= give
                allocations[resource] = allocations.get(resource, 0) + give
        rec["status"] = "responding"
        # Unmet need after this dispatch: need minus prior allocations
        # minus what this dispatch just allocated.
        base = self.need(iid)
        prior = self._allocated(iid)
        unmet_after = {r: q - prior.get(r, 0) - allocations.get(r, 0)
                       for r, q in base.items()
                       if q - prior.get(r, 0) - allocations.get(r, 0) > 0}
        disp = {"incident": iid, "locality": rec["locality"],
                "dispatched_at": _utcnow(), "allocations": allocations,
                "unmet": unmet_after,
                "note": "planning units from severity table, not promises",
                "source": SOURCE_LABEL}
        self._dispatches.append(disp)
        self._save()
        return disp

    def dispatches(self, iid=None):
        ds = list(self._dispatches)
        if iid is not None:
            ds = [d for d in ds if d["incident"] == iid]
        return ds
