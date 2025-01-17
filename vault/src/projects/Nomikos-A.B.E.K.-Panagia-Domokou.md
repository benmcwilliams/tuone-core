```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GRC-08329-09563") and reject-phase = false
sort location, company asc
```
