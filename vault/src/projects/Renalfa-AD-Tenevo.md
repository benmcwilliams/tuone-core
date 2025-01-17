```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BGR-08754-09847") and reject-phase = false
sort location, company asc
```
