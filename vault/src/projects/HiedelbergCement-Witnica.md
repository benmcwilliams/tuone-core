```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-04113-09140") and reject-phase = false
sort location, company asc
```
