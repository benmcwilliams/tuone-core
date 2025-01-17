```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-10279-10448") and reject-phase = false
sort location, company asc
```
