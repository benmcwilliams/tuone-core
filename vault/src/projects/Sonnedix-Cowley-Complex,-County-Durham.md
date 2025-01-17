```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-07976-04275") and reject-phase = false
sort location, company asc
```
