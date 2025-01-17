```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "GBR-04591-06496") and reject-phase = false
sort location, company asc
```
