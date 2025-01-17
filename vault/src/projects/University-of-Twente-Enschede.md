```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-07952-10302") and reject-phase = false
sort location, company asc
```
