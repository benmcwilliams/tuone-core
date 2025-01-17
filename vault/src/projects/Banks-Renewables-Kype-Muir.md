```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-08091-01469") and reject-phase = false
sort location, company asc
```
