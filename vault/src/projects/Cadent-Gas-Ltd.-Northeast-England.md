```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-03496-08487") and reject-phase = false
sort location, company asc
```
