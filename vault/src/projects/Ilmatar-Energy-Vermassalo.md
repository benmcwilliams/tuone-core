```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "FIN-09130-09204") and reject-phase = false
sort location, company asc
```
