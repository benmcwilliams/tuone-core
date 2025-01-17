```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BGR-01032-09262") and reject-phase = false
sort location, company asc
```
