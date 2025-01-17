```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ISL-04772-07757") and reject-phase = false
sort location, company asc
```
