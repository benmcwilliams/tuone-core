```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-03185-03472") and reject-phase = false
sort location, company asc
```
