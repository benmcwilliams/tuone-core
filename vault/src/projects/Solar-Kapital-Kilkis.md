```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GRC-03711-04257") and reject-phase = false
sort location, company asc
```
