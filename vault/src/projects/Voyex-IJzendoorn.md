```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-03188-10372") and reject-phase = false
sort location, company asc
```
