```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ITA-00713-01235") and reject-phase = false
sort location, company asc
```
