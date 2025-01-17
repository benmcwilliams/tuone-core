```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "CZE-08231-10494") and reject-phase = false
sort location, company asc
```
