```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-09485-00822") and reject-phase = false
sort location, company asc
```
