from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import service

ROOT = Path(__file__).parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

df = pd.read_csv(ROOT / "tickets.csv")
dev, ev = df[df.split == "development"], df[df.split == "eval"].reset_index(drop=True)
labels = list(service.CATEGORIES) + ["unknown"]

BASE = {"password_reset": "password", "wifi_network": "wifi", "email_issue": "email", "software_install": "install",
        "lms_access": "moodle", "printing": "print", "hardware_fault": "laptop", "vpn_remote": "vpn",
        "classroom_av": "projector", "security_incident": "phishing"}

errors = {}


def baseline(t):
    t = t.lower()
    return next((c for c, k in BASE.items() if k in t), "unknown")


def model(v):
    def f(t):
        try:
            return service.analyze(t, v)["category"]
        except service.BackendUnavailable as e:
            raise SystemExit(f"Live backend failed, stopping: {str(e)[:300]}")
        except service.TicketError as e:
            errors.setdefault(v, str(e))  
            return "unknown"
    return f


run_mode = service.mode()  

vec = TfidfVectorizer(stop_words="english").fit(dev.ticket)
sims = cosine_similarity(vec.transform(ev.ticket), vec.transform(dev.ticket))
preds = {
    "keyword_baseline": [baseline(t) for t in ev.ticket],
    "tfidf_cosine_1nn": list(dev.expected_category.values[sims.argmax(axis=1)]),
    f"{run_mode}_prompt_v1": [model("v1")(t) for t in ev.ticket],
    f"{run_mode}_prompt_v2": [model("v2")(t) for t in ev.ticket],
}

note = ("mock scores are fixture results, not LLM performance"
        if run_mode == "mock" else "scores come from real LLM calls")
print(f"Eval set: {len(ev)} tickets (mode: {run_mode}; {note})\n")

for name, p in preds.items():
    acc = (pd.Series(p) == ev.expected_category).mean()
    print(f"{name:20s} accuracy = {acc:.2f}")
    cm = (pd.crosstab(ev.expected_category, pd.Series(p, name="predicted"))
            .reindex(index=labels[:-1], columns=labels, fill_value=0))
    cm.to_csv(RESULTS / f"confusion_{name}.csv")
    for t, e, g in zip(ev.ticket, ev.expected_category, p):
        if e != g:
            print(f"   ERR expected={e} got={g} :: {t}")

for v, msg in errors.items():
    print(f"\nFirst {v} output rejected: {msg[:300]}")

print("\nDev category counts:\n", dev.expected_category.value_counts().to_dict())