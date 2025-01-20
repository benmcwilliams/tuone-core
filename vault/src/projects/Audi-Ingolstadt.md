```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "HUN-00514-00061") and reject-phase = false
sort location, company asc
```
