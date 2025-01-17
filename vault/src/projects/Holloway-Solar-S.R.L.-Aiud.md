```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ROU-04807-05254") and reject-phase = false
sort location, company asc
```
