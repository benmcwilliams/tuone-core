```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-09125-09205") and reject-phase = false
sort location, company asc
```
