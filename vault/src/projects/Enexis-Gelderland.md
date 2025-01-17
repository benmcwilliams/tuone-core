```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-06320-06479") and reject-phase = false
sort location, company asc
```
