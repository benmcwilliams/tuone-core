```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BGR-10263-08179") and reject-phase = false
sort location, company asc
```
