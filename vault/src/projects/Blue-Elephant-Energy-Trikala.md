```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GRC-08175-06762") and reject-phase = false
sort location, company asc
```
