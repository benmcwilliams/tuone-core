```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BGR-10000-06078") and reject-phase = false
sort location, company asc
```
