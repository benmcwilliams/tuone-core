```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Domum Urban Mobility"
sort location, dt_announce desc
```
