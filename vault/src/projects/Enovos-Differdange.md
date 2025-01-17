```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "LUX-08011-08825") and reject-phase = false
sort location, company asc
```
