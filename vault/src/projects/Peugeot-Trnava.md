```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SVK-01137-00611") and reject-phase = false
sort location, company asc
```
