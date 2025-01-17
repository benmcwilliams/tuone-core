```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DEU-08000-08300") and reject-phase = false
sort location, company asc
```
