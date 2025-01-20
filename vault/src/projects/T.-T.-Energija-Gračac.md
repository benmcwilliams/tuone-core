```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "HRV-10069-10179") and reject-phase = false
sort location, company asc
```
