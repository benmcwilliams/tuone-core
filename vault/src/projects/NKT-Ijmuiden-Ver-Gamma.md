```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-09426-07937") and reject-phase = false
sort location, company asc
```
