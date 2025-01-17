```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-01139-00241") and reject-phase = false
sort location, company asc
```
