```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Merlin-Properties" or company = "Merlin Properties")
sort location, dt_announce desc
```
