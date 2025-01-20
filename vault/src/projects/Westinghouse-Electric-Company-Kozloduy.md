```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where contains(file.name, "BGR-07912-07524") and reject-phase = false
sort location, company asc
```
