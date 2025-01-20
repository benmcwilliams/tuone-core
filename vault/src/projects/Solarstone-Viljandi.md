```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "EST-03207-03501") and reject-phase = false
sort location, company asc
```
