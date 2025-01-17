```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BEL-00366-08769") and reject-phase = false
sort location, company asc
```
