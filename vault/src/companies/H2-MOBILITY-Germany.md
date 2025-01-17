```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "H2 Mobility Germany"
sort location, dt_announce desc
```
