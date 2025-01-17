```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GRC-04517-04964") and reject-phase = false
sort location, company asc
```
