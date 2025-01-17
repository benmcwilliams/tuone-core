```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "LTU-07520-07887") and reject-phase = false
sort location, company asc
```
