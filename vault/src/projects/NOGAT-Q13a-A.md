```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-04319-05634") and reject-phase = false
sort location, company asc
```
