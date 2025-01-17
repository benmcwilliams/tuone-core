```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-00018-05819") and reject-phase = false
sort location, company asc
```
