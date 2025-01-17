```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-00254-00712") and reject-phase = false
sort location, company asc
```
