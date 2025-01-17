```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BGR-09716-09781") and reject-phase = false
sort location, company asc
```
