```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-03797-09399") and reject-phase = false
sort location, company asc
```
