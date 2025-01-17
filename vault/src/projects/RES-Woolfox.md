```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-09760-01883") and reject-phase = false
sort location, company asc
```
