```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-01249-00440") and reject-phase = false
sort location, company asc
```
