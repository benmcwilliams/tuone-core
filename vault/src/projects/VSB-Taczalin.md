```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "POL-10158-10320") and reject-phase = false
sort location, company asc
```
