```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-00355-00412") and reject-phase = false
sort location, company asc
```
