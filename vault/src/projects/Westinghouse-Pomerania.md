```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-08136-08179") and reject-phase = false
sort location, company asc
```
