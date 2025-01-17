```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-09634-09675") and reject-phase = false
sort location, company asc
```
