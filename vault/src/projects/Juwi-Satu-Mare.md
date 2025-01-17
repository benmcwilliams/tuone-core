```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ROU-09217-03113") and reject-phase = false
sort location, company asc
```
