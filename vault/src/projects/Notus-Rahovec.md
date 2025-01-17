```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DEU-06951-09593") and reject-phase = false
sort location, company asc
```
