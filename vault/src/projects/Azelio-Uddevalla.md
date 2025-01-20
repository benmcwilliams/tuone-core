```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "SWE-01679-00932") and reject-phase = false
sort location, company asc
```
