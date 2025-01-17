```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "POL-03653-05721") and reject-phase = false
sort location, company asc
```
