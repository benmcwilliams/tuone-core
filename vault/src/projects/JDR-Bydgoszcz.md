```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-08998-09266") and reject-phase = false
sort location, company asc
```
