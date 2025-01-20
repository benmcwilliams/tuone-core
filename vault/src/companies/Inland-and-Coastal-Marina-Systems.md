```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "Inland and Coastal Marina Systems"
sort location, dt_announce desc
```
