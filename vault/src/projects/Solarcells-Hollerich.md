```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "LUX-03193-03486") and reject-phase = false
sort location, company asc
```
