```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "LTU-05055-07919") and reject-phase = false
sort location, company asc
```
