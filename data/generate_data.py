"""
Generate realistic sample agent_runs data for the GTM AI Workflow Simulator.
Produces 200+ rows spanning 45 days with realistic distributions.
"""
import csv
import random
from datetime import datetime, timedelta

random.seed(42)

# --- Configuration ---
OUTPUT_FILE = "sample_agent_runs.csv"
NUM_ROWS = 220
START_DATE = datetime(2026, 1, 1, 8, 0, 0)
END_DATE = datetime(2026, 2, 14, 17, 0, 0)

TASK_TYPES = ["lead_summary", "follow_up", "risk_analysis", "data_hygiene"]
TASK_WEIGHTS = [0.35, 0.25, 0.25, 0.15]

LEAD_SOURCES = [
    "Inbound - Webinar", "Inbound - Demo Request", "Inbound - Whitepaper",
    "Inbound - Website", "Outbound - Cold", "Outbound - Enterprise",
    "Event - Summit", "Event - Workshop", "Partner Referral", "PLG - Free Trial"
]

CRM_STAGES = [
    "MQL", "SAL", "SQL", "Discovery", "Technical Validation",
    "Value/Impact", "Negotiation", "Closed Won", "Closed Lost"
]
CRM_STAGE_WEIGHTS = [0.18, 0.12, 0.14, 0.16, 0.12, 0.10, 0.08, 0.06, 0.04]

WORKFLOW_STAGES = {
    "lead_summary": "Pipeline Generation",
    "follow_up": "Deal Execution",
    "risk_analysis": "Deal Execution",
    "data_hygiene": "Onboarding & Adoption",
}

PROMPT_VERSIONS = ["v1.0", "v1.1", "v1.2", "v2.0"]
PROMPT_VERSION_WEIGHTS = [0.15, 0.25, 0.35, 0.25]  # v2.0 is latest

USER_IDS = [f"USR{str(i).zfill(3)}" for i in range(101, 131)]  # 30 users

# --- Helper functions ---

def random_timestamp(start, end):
    """Generate random datetime between start and end, during business hours."""
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    dt = start + timedelta(seconds=random_seconds)
    # Clamp to business hours (8 AM - 6 PM), skip weekends
    while dt.weekday() >= 5:  # Saturday=5, Sunday=6
        dt += timedelta(days=1)
    dt = dt.replace(hour=random.randint(8, 17), minute=random.randint(0, 59),
                    second=random.randint(0, 59))
    return dt


def generate_opportunity_value(crm_stage, task_type):
    """Generate realistic opportunity value based on CRM stage."""
    if task_type == "lead_summary" and crm_stage in ("MQL", "SAL"):
        return 0  # Not yet qualified
    if crm_stage in ("Closed Lost",):
        return random.choice([0, random.randint(10000, 200000)])
    if crm_stage in ("Closed Won",):
        return random.randint(25000, 600000)
    if crm_stage in ("Negotiation", "Value/Impact"):
        return random.randint(50000, 500000)
    if crm_stage in ("Technical Validation",):
        return random.randint(30000, 350000)
    if crm_stage in ("Discovery", "SQL"):
        return random.randint(10000, 150000)
    return random.choice([0, random.randint(5000, 50000)])


def generate_time_saved(task_type):
    """Estimate minutes saved by AI vs manual process."""
    base = {
        "lead_summary": (8, 20),     # Research that used to take 15-30 min
        "follow_up": (5, 15),        # Drafting follow-ups
        "risk_analysis": (10, 25),   # Pulling together risk signals
        "data_hygiene": (3, 10),     # Manual data cleanup
    }
    lo, hi = base.get(task_type, (5, 15))
    return round(random.uniform(lo, hi), 1)


def generate_row(run_id, timestamps_sorted, idx):
    """Generate a single agent_runs row."""
    timestamp = timestamps_sorted[idx]
    task_type = random.choices(TASK_TYPES, weights=TASK_WEIGHTS, k=1)[0]
    
    # Agent version: 70% A, 30% B
    agent_version = random.choices(["A", "B"], weights=[0.70, 0.30], k=1)[0]
    
    # Prompt version: later dates skew toward newer versions
    day_ratio = idx / len(timestamps_sorted)
    if day_ratio < 0.25:
        prompt_version = random.choices(PROMPT_VERSIONS[:2], weights=[0.6, 0.4], k=1)[0]
    elif day_ratio < 0.60:
        prompt_version = random.choices(PROMPT_VERSIONS[1:3], weights=[0.4, 0.6], k=1)[0]
    else:
        prompt_version = random.choices(PROMPT_VERSIONS[2:], weights=[0.4, 0.6], k=1)[0]
    
    # Resolution time: Agent A faster on average
    if agent_version == "A":
        resolution_time = round(random.gauss(3.5, 0.8), 2)
    else:
        resolution_time = round(random.gauss(5.2, 1.2), 2)
    resolution_time = max(1.0, min(resolution_time, 12.0))
    
    # User acceptance: Agent A ~90%, Agent B ~72%
    if agent_version == "A":
        user_accepted = random.random() < 0.90
    else:
        user_accepted = random.random() < 0.72
    
    # User rating: correlated with acceptance
    if user_accepted:
        user_rating = random.choices([3, 4, 5], weights=[0.1, 0.35, 0.55], k=1)[0]
    else:
        user_rating = random.choices([1, 2, 3], weights=[0.3, 0.5, 0.2], k=1)[0]
    
    # Abstention (escalation): ~5% overall
    abstained = random.random() < 0.05
    if abstained:
        user_accepted = False
        user_rating = random.choice([2, 3])
    
    # Errors: ~3% for A, ~8% for B
    error_rate = 0.03 if agent_version == "A" else 0.08
    error_occurred = random.random() < error_rate
    if error_occurred:
        user_accepted = False
        user_rating = 1
    
    lead_source = random.choice(LEAD_SOURCES)
    crm_stage = random.choices(CRM_STAGES, weights=CRM_STAGE_WEIGHTS, k=1)[0]
    opportunity_value = generate_opportunity_value(crm_stage, task_type)
    workflow_stage = WORKFLOW_STAGES.get(task_type, "Pipeline Generation")
    time_saved = generate_time_saved(task_type)
    user_id = random.choice(USER_IDS)
    
    return {
        "run_id": f"RUN{str(run_id).zfill(3)}",
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "task_type": task_type,
        "agent_version": agent_version,
        "resolution_time_seconds": resolution_time,
        "user_accepted": user_accepted,
        "user_rating": user_rating,
        "abstained": abstained,
        "error_occurred": error_occurred,
        "lead_source": lead_source,
        "crm_stage": crm_stage,
        "opportunity_value": opportunity_value,
        "workflow_stage": workflow_stage,
        "time_saved_minutes": time_saved,
        "prompt_version": prompt_version,
    }


def main():
    # Generate sorted timestamps
    timestamps = sorted([random_timestamp(START_DATE, END_DATE) for _ in range(NUM_ROWS)])
    
    rows = []
    for i in range(NUM_ROWS):
        row = generate_row(i + 1, timestamps, i)
        rows.append(row)
    
    # Write CSV
    fieldnames = list(rows[0].keys())
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    # Stats
    total = len(rows)
    accepted = sum(1 for r in rows if r["user_accepted"])
    version_a = [r for r in rows if r["agent_version"] == "A"]
    version_b = [r for r in rows if r["agent_version"] == "B"]
    time_saved_total = sum(r["time_saved_minutes"] for r in rows)
    
    print(f"✅ Generated {total} rows → {OUTPUT_FILE}")
    print(f"   Date range: {timestamps[0].strftime('%Y-%m-%d')} to {timestamps[-1].strftime('%Y-%m-%d')}")
    print(f"   Acceptance rate: {accepted/total*100:.1f}%")
    print(f"   Agent A: {len(version_a)} runs, {sum(1 for r in version_a if r['user_accepted'])/len(version_a)*100:.1f}% accepted")
    print(f"   Agent B: {len(version_b)} runs, {sum(1 for r in version_b if r['user_accepted'])/len(version_b)*100:.1f}% accepted")
    print(f"   Total time saved: {time_saved_total:.0f} minutes ({time_saved_total/60:.1f} hours)")
    print(f"   Unique users: {len(set(r['user_id'] for r in rows))}")
    print(f"   Prompt versions: {', '.join(sorted(set(r['prompt_version'] for r in rows)))}")


if __name__ == "__main__":
    main()
