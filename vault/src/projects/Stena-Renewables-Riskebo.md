```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "SWE-08381-10119") and reject-phase = false
sort location, company asc
```
