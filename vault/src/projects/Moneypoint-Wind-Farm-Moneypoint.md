```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "IRL-04418-09489") and reject-phase = false
sort location, company asc
```
