```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "LVA-10058-10149") and reject-phase = false
sort location, company asc
```
