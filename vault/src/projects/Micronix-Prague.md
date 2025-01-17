```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "CZE-00885-09475") and reject-phase = false
sort location, company asc
```
