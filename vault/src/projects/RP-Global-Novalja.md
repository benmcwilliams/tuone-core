```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "HRV-05427-05877") and reject-phase = false
sort location, company asc
```
