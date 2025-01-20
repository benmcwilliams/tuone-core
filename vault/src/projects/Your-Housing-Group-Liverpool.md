```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "GBR-01605-03743") and reject-phase = false
sort location, company asc
```
