#!/usr/bin/env python3
"""the-safety-net CLI: welfare core for a new nation.

Subcommands:
  benefits enroll --id ID --program P --amount USD --schedule S
                   P in: retirement, disability, survivor, child, other
                   S in: monthly, biweekly, weekly
  benefits beneficiaries [--program P]
  benefits run [--at ISO]
  benefits payments [--id ID]
  benefits due
  benefits on-time [--days N]
  benefits summary
  disaster stock --depot D --resource R --quantity Q
                   R in: water, food, shelter_kits, medical, generators,
                   blankets, fuel, other
  disaster inventory [--depot D]
  disaster report --type T --locality L --severity 1-5
                   T in: flood, fire, storm, earthquake, drought,
                   pandemic, other
  disaster incidents [--status S]   S in: open, responding, resolved
  disaster need --incident IID
  disaster dispatch --incident IID
  disaster unmet --incident IID
  disaster resolve --incident IID
  diplomacy log --counterparty C --type T --date YYYY-MM-DD --summary S
                  [--status ST] [--review-date YYYY-MM-DD]
                  T in: treaty, notice, summit, communique
                  ST in: active, pending, expired, withdrawn
  diplomacy entries [--counterparty C] [--status ST] [--type T]
  diplomacy set-status --id EID --status ST
  diplomacy obligations [--within-days N]
  diplomacy summary

Global: --data-dir DIR (default: data/)
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from benefits import Benefits, PROGRAMS, SCHEDULES
from disaster import (Disaster, SEVERITIES, STATUSES, INCIDENT_TYPES,
                      RESOURCE_TYPES)
from diplomacy import Diplomacy, ENTRY_TYPES, ENTRY_STATUSES


def _pct(x):
    return "n/a" if x is None else "%.1f%%" % x


def _j(obj):
    print(json.dumps(obj, indent=2))


def _add_benefits(sub):
    b = sub.add_parser("benefits", help="benefits ledger")
    bs = b.add_subparsers(dest="cmd", required=True)

    p = bs.add_parser("enroll", help="enroll a beneficiary")
    p.add_argument("--id", required=True)
    p.add_argument("--program", required=True, choices=PROGRAMS)
    p.add_argument("--amount", required=True, type=float)
    p.add_argument("--schedule", required=True, choices=SCHEDULES)

    p = bs.add_parser("beneficiaries", help="list beneficiaries")
    p.add_argument("--program", choices=PROGRAMS, default=None)

    p = bs.add_parser("run", help="pay every due beneficiary")
    p.add_argument("--at", default=None, help="ISO timestamp override")

    p = bs.add_parser("payments", help="list payments")
    p.add_argument("--id", default=None)

    bs.add_parser("due", help="beneficiaries with a payment due")

    p = bs.add_parser("on-time", help="on-time payment rate")
    p.add_argument("--days", type=int, default=90)

    bs.add_parser("summary", help="ledger health summary")


def _add_disaster(sub):
    d = sub.add_parser("disaster", help="disaster coordination")
    ds = d.add_subparsers(dest="cmd", required=True)

    p = ds.add_parser("stock", help="add resource stock to a depot")
    p.add_argument("--depot", required=True)
    p.add_argument("--resource", required=True, choices=RESOURCE_TYPES)
    p.add_argument("--quantity", required=True, type=float)

    p = ds.add_parser("inventory", help="show inventory")
    p.add_argument("--depot", default=None)

    p = ds.add_parser("report", help="open an incident record")
    p.add_argument("--type", required=True, choices=INCIDENT_TYPES)
    p.add_argument("--locality", required=True)
    p.add_argument("--severity", required=True, type=int, choices=SEVERITIES)

    p = ds.add_parser("incidents", help="list incidents")
    p.add_argument("--status", default=None, choices=STATUSES)

    p = ds.add_parser("need", help="estimated need for an incident")
    p.add_argument("--incident", required=True)

    p = ds.add_parser("dispatch", help="allocate stock to an incident")
    p.add_argument("--incident", required=True)

    p = ds.add_parser("unmet", help="unmet need for an incident")
    p.add_argument("--incident", required=True)

    p = ds.add_parser("resolve", help="mark an incident resolved")
    p.add_argument("--incident", required=True)


def _add_diplomacy(sub):
    d = sub.add_parser("diplomacy", help="treaty and communications log")
    ds = d.add_subparsers(dest="cmd", required=True)

    p = ds.add_parser("log", help="record a diplomatic entry")
    p.add_argument("--counterparty", required=True)
    p.add_argument("--type", required=True, choices=ENTRY_TYPES)
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--summary", required=True)
    p.add_argument("--status", default="active", choices=ENTRY_STATUSES)
    p.add_argument("--review-date", default=None, help="YYYY-MM-DD")

    p = ds.add_parser("entries", help="list log entries")
    p.add_argument("--counterparty", default=None)
    p.add_argument("--status", default=None, choices=ENTRY_STATUSES)
    p.add_argument("--type", default=None, choices=ENTRY_TYPES)

    p = ds.add_parser("set-status", help="change an entry's status")
    p.add_argument("--id", required=True)
    p.add_argument("--status", required=True, choices=ENTRY_STATUSES)

    p = ds.add_parser("obligations", help="upcoming review obligations")
    p.add_argument("--within-days", type=int, default=90)

    ds.add_parser("summary", help="log summary")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="safety_net_cli.py",
                                 description="the-safety-net: welfare core")
    ap.add_argument("--data-dir", default="data/",
                    help="registry storage directory")
    sub = ap.add_subparsers(dest="area", required=True)
    _add_benefits(sub)
    _add_disaster(sub)
    _add_diplomacy(sub)
    args = ap.parse_args(argv)

    if args.area == "benefits":
        b = Benefits(args.data_dir)
        c = args.cmd
        if c == "enroll":
            _j(b.enroll(args.id, args.program, args.amount, args.schedule))
        elif c == "beneficiaries":
            _j(b.beneficiaries(program=args.program))
        elif c == "run":
            pays = b.run_payments(at=args.at)
            print("paid %d payment(s)" % len(pays))
            _j(pays)
        elif c == "payments":
            _j(b.payments(bid=args.id))
        elif c == "due":
            due = b.due_beneficiaries()
            print("%d due" % len(due))
            _j([{"beneficiary": bid, "due_date": dd.isoformat()}
                for bid, dd in due])
        elif c == "on-time":
            rate, due_n, on_n = b.on_time_rate(days=args.days)
            print("on-time rate (%dd): %s (%d of %d due)"
                  % (args.days, _pct(None if rate is None else rate * 100),
                     on_n, due_n))
        elif c == "summary":
            _j(b.summary())

    elif args.area == "disaster":
        d = Disaster(args.data_dir)
        c = args.cmd
        if c == "stock":
            _j(d.stock(args.depot, args.resource, args.quantity))
        elif c == "inventory":
            _j(d.inventory(depot=args.depot))
        elif c == "report":
            _j(d.report_incident(args.type, args.locality, args.severity))
        elif c == "incidents":
            _j(d.incidents(status=args.status))
        elif c == "need":
            _j(d.need(args.incident))
        elif c == "dispatch":
            disp = d.dispatch(args.incident)
            print("dispatched to %s (%s): %d resource line(s), "
                  "unmet: %s" % (
                      disp["incident"], disp["locality"],
                      len(disp["allocations"]),
                      ", ".join("%s %s" % (v, k)
                                for k, v in disp["unmet"].items())
                      or "none"))
            _j(disp)
        elif c == "unmet":
            _j(d.unmet_need(args.incident))
        elif c == "resolve":
            _j(d.resolve(args.incident))

    elif args.area == "diplomacy":
        d = Diplomacy(args.data_dir)
        c = args.cmd
        if c == "log":
            _j(d.log(args.counterparty, args.type, args.date, args.summary,
                     status=args.status, review_date=args.review_date))
        elif c == "entries":
            _j(d.entries(counterparty=args.counterparty, status=args.status,
                         etype=args.type))
        elif c == "set-status":
            _j(d.set_status(args.id, args.status))
        elif c == "obligations":
            ob = d.obligations(within_days=args.within_days)
            print("%d obligation(s) within %d days"
                  % (len(ob), args.within_days))
            _j(ob)
        elif c == "summary":
            _j(d.summary())


if __name__ == "__main__":
    main()
