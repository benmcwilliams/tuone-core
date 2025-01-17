```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Grupa Azoty Zakłady Chemiczne Police SA"
sort location, dt_announce desc
```
