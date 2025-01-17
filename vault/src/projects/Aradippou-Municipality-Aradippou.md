```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "CYP-08009-08303") and reject-phase = false
sort location, company asc
```
