```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "EST-05216-05654") and reject-phase = false
sort location, company asc
```
