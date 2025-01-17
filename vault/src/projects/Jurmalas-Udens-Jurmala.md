```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "LVA-08371-09302") and reject-phase = false
sort location, company asc
```
