```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-08370-05688") and reject-phase = false
sort location, company asc
```
