```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-04408-09452") and reject-phase = false
sort location, company asc
```
