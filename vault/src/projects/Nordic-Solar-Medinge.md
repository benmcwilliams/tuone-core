```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-09028-07957") and reject-phase = false
sort location, company asc
```
