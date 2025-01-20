```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "GRC-08853-08942") and reject-phase = false
sort location, company asc
```
