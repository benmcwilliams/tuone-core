```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-05284-01455") and reject-phase = false
sort location, company asc
```
