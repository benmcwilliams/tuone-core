```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-01027-00966") and reject-phase = false
sort location, company asc
```
