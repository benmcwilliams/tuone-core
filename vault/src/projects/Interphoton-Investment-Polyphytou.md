```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "GRC-09175-09248") and reject-phase = false
sort location, company asc
```
