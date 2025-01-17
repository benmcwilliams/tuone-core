```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-01021-01023") and reject-phase = false
sort location, company asc
```
