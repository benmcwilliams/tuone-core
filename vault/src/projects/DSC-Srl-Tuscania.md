```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "ITA-06301-07403") and reject-phase = false
sort location, company asc
```
