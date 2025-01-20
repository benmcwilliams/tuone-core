```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "DEU-01529-08628") and reject-phase = false
sort location, company asc
```
