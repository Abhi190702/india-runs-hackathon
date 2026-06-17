# Honeypot Detection

Hard honeypots are internally impossible profiles: jobs ending before they start, current jobs with end dates, future job starts, current-job duration that contradicts elapsed time, impossible tenure math, education ending before it starts, and clusters of expert skills with zero months used plus weak endorsement proof.

Soft anomalies are risk signals rather than automatic rejection: AI keyword stuffing, wrong-domain roles with weak career evidence, shallow chatbot-only profiles, pure research without deployment, consulting-only weak fit, inactive candidates, low response rates, long notice, and outside-India logistics risk.

Embeddings cannot detect impossible dates or contradictory durations. That is why V2 uses explicit logical checks, penalties, and score caps.

| Type | Example | Action |
| --- | --- | --- |
| Hard honeypot | Demo F: current role duration exceeds elapsed time, or 3+ expert skills have 0 months and weak endorsements | Heavy penalty and score cap |
| Soft anomaly | Demo E: HR/marketing profile with AI terms mostly in skills | Penalty and possible cap |
| Logistics risk | Outside India without relocation, long notice, inactive profile | Lower hireability and cap when severe |

Caps are used because a suspicious profile can still have some relevant text. The cap prevents a profile with impossible or weakly supported claims from floating above career-backed engineers.
