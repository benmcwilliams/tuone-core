```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "POL-03653-09659") and reject-phase = false
sort location, company asc
```
