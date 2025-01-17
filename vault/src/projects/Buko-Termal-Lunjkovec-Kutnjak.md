```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "HRV-08211-08447") and reject-phase = false
sort location, company asc
```
