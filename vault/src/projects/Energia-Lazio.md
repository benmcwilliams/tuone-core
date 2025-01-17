```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ITA-03732-07420") and reject-phase = false
sort location, company asc
```
