```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DEU-00213-08894") and reject-phase = false
sort location, company asc
```
