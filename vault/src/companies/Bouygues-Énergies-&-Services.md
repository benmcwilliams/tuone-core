```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Bouygues Énergies & Services"
sort location, dt_announce desc
```
