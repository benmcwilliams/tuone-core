```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ITA-00878-10496") and reject-phase = false
sort location, company asc
```
