```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-05984-06538") and reject-phase = false
sort location, company asc
```
