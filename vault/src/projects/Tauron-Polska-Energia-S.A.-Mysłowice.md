```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-10074-10199") and reject-phase = false
sort location, company asc
```
