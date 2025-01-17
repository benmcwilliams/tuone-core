```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BGR-09448-09539") and reject-phase = false
sort location, company asc
```
