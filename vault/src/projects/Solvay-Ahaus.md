```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DEU-05908-00727") and reject-phase = false
sort location, company asc
```
