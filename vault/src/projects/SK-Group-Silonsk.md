```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-01019-00685") and reject-phase = false
sort location, company asc
```
