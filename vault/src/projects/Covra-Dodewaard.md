```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "NLD-08356-08567") and reject-phase = false
sort location, company asc
```
