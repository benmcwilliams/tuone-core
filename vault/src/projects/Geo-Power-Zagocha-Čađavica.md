```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "HRV-08891-08987") and reject-phase = false
sort location, company asc
```
