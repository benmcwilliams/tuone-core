```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-08838-01663") and reject-phase = false
sort location, company asc
```
