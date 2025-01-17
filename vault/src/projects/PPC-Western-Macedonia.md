```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GRC-01234-05766") and reject-phase = false
sort location, company asc
```
