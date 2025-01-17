```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-08898-09003") and reject-phase = false
sort location, company asc
```
