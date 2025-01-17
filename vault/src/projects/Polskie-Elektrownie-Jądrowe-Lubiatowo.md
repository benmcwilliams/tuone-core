```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-09705-09759") and reject-phase = false
sort location, company asc
```
