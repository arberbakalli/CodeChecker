#!/usr/bin/env python3
"""
Backfill GitHub contribution graph from 2015-01-01 to yesterday.
Usage: python backfill.py | git fast-import && git push
"""
import random, sys, calendar, datetime
from datetime import date, timedelta

random.seed(1337)

# Parent SHA passed as first arg (run: python backfill.py $(git rev-parse HEAD) | git fast-import)
PARENT_SHA = sys.argv[1] if len(sys.argv) > 1 else None

START  = date(2015, 1, 1)
END    = date(2026, 7, 20)
AUTHOR = "arberbakalli"
EMAIL  = "arberbakalli@pm.me"
BRANCH = "refs/heads/master"

MSGS = [
    "chore(bot): \U0001f602 auto commit",
    "chore(bot): \U0001f631 auto commit",
    "chore(bot): \U0001f47f auto commit",
    "chore(bot): \U0001f4a9 auto commit",
    "chore(bot): \U0001f64f auto commit",
    "chore(bot): \U0001f648 auto commit",
    "chore(bot): \U0001f410 auto commit",
    "chore(bot): \U0001f916 auto commit",
    "chore(bot): \U0001f7e9 auto commit",
    "chore(bot): \U0001f47b auto commit",
]

# --- build schedule of burst days and active sprint weeks ---
burst_days   = set()
active_weeks = set()

d = START
next_burst = d + timedelta(days=random.randint(90, 180))
while d <= END:
    if d >= next_burst:
        for i in range(random.randint(1, 2)):
            bd = d + timedelta(days=i)
            if bd <= END:
                burst_days.add(bd)
        next_burst = d + timedelta(days=random.randint(90, 180))
    if random.random() < 0.25:
        iso = d.isocalendar()
        active_weeks.add((iso[0], iso[1]))
    d += timedelta(days=7)

def commit_count(d):
    # Major holidays — likely off
    if (d.month == 12 and d.day in (24, 25, 26, 31)) or \
       (d.month ==  1 and d.day ==  1):
        return 0 if random.random() < 0.75 else random.randint(1, 3)

    if d in burst_days:
        return random.randint(20, 60)

    iso    = d.isocalendar()
    active = (iso[0], iso[1]) in active_weeks

    if d.weekday() >= 5:  # weekend
        if random.random() < 0.28:
            return 0
        return random.randint(10, 30) if active else random.randint(2, 7)
    else:                 # weekday
        if random.random() < 0.07:
            return 0
        return random.randint(10, 30) if active else random.randint(4, 10)

# --- emit git fast-import stream ---
out   = sys.stdout.buffer
mark  = 1
first = True

d = START
total = 0
while d <= END:
    n = commit_count(d)
    if n:
        times = sorted(
            (random.randint(7, 23), random.randint(0, 59), random.randint(0, 59))
            for _ in range(n)
        )
        for h, mi, s in times:
            ts      = int(calendar.timegm(
                          datetime.datetime(d.year, d.month, d.day, h, mi, s).timetuple()))
            msg     = random.choice(MSGS).encode("utf-8")
            content = f"{d.isoformat()}T{h:02d}:{mi:02d}:{s:02d}Z\n".encode("utf-8")

            out.write(f"commit {BRANCH}\n".encode())
            out.write(f"mark :{mark}\n".encode())
            out.write(f"author {AUTHOR} <{EMAIL}> {ts} +0000\n".encode())
            out.write(f"committer {AUTHOR} <{EMAIL}> {ts} +0000\n".encode())
            out.write(f"data {len(msg)}\n".encode())
            out.write(msg)
            out.write(b"\n")
            if first and PARENT_SHA:
                out.write(f"from {PARENT_SHA}\n".encode())
                first = False
            out.write(b"M 100644 inline LAST_UPDATED\n")
            out.write(f"data {len(content)}\n".encode())
            out.write(content)
            out.write(b"\n")

            mark += 1
            total += 1
    d += timedelta(days=1)

out.flush()
sys.stderr.write(f"Stream complete: {total} commits across {(END - START).days} days\n")
