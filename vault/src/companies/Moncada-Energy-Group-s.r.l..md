```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Moncada Energy Group s.r.l."
sort location, dt_announce desc
```
