```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "Heide town's municipal utility"
sort location, dt_announce desc
```
