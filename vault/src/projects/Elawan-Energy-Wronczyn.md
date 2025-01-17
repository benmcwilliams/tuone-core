```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-08535-07720") and reject-phase = false
sort location, company asc
```
