```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "MLT-10109-10297") and reject-phase = false
sort location, company asc
```
