```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-07523-01626") and reject-phase = false
sort location, company asc
```
