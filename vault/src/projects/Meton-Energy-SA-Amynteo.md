```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GRC-05151-05581") and reject-phase = false
sort location, company asc
```
