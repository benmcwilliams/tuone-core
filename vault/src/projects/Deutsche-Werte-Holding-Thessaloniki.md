```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GRC-03064-08629") and reject-phase = false
sort location, company asc
```
