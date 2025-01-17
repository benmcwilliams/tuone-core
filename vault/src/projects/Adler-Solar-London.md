```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-00647-08255") and reject-phase = false
sort location, company asc
```
