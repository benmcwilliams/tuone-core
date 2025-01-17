```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DEU-00353-10139") and reject-phase = false
sort location, company asc
```
