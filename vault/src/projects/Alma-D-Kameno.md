```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where contains(file.name, "BGR-07962-08275") and reject-phase = false
sort location, company asc
```
