```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BGR-01146-03452") and reject-phase = false
sort location, company asc
```
