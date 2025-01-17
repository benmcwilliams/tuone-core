```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "SWE-05952-00351") and reject-phase = false
sort location, company asc
```
