```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-08165-00952") and reject-phase = false
sort location, company asc
```
