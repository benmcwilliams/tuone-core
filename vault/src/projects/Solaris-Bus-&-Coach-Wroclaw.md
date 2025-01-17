```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-01249-01950") and reject-phase = false
sort location, company asc
```
