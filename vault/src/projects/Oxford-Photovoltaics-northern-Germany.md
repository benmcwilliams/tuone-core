```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DEU-03067-03269") and reject-phase = false
sort location, company asc
```
