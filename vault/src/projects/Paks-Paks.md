```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "HUN-07921-09704") and reject-phase = false
sort location, company asc
```
