```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ROU-00351-00069") and reject-phase = false
sort location, company asc
```
