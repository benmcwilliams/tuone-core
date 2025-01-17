```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-01723-08978") and reject-phase = false
sort location, company asc
```
