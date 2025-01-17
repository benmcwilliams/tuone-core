```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "DEU-00601-00449") and reject-phase = false
sort location, company asc
```
