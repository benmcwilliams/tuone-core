```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "HRV-01279-01089") and reject-phase = false
sort location, company asc
```
