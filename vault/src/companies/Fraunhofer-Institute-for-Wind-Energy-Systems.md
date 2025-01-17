```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Fraunhofer Institute for Wind Energy Systems"
sort location, dt_announce desc
```
