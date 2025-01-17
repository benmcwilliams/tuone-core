```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Eoliennes en Mer Dieppe Le Tréport"
sort location, dt_announce desc
```
