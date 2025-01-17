```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-07973-01447") and reject-phase = false
sort location, company asc
```
