```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "CHE-09832-09858") and reject-phase = false
sort location, company asc
```
