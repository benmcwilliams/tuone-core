```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-00867-00032") and reject-phase = false
sort location, company asc
```
