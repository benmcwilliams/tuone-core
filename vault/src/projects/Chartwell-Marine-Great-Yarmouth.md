```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-07953-08519") and reject-phase = false
sort location, company asc
```
