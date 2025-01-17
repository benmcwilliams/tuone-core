```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-09639-08175") and reject-phase = false
sort location, company asc
```
