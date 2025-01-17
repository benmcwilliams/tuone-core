```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ITA-06090-07461") and reject-phase = false
sort location, company asc
```
