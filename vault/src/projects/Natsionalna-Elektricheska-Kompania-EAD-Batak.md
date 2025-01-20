```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "BGR-09447-09539") and reject-phase = false
sort location, company asc
```
