```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-08408-08818") and reject-phase = false
sort location, company asc
```
