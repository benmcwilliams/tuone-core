```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "SWE-01319-04081") and reject-phase = false
sort location, company asc
```
