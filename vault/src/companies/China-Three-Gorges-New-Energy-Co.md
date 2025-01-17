```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "China Three Gorges New Energy Co"
sort location, dt_announce desc
```
