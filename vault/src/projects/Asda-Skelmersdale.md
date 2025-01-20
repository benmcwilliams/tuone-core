```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "GBR-03408-03802") and reject-phase = false
sort location, company asc
```
